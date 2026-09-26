"""Reproducible Q5 STM32L072CBT6 build; EEPROM and option bytes never loaded by the image."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from test_firmware_q5 import run_tests
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'firmware/q5-stm32'
STEM='count-fidget-Q5-stm32'
SOURCES=('startup.c','main_stm32.c','runtime.c','counter.c','input.c','journal.c','app.c','fram.c','oled.c','rail.c','battery.c')
FLAGS=('-mcpu=cortex-m0plus','-mthumb','-std=c11','-Os','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-fstack-usage')
SUFFIXES=('.elf','.hex','.bin','.map','.lst')
OUTPUTS=tuple(STEM+s for s in SUFFIXES)+('stack-usage.txt','host-tests.json')
def record(p):
    data=p.read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def inputs():
    files=[p for p in SOURCE.rglob('*') if p.is_file() and 'build' not in p.relative_to(SOURCE).parts and p.suffix in ('.c','.h','.ld','.md','.txt','.json')]
    files += [ROOT/'scripts/build_firmware_q5.py',ROOT/'scripts/test_firmware_q5.py']
    return {p.relative_to(ROOT).as_posix():record(p) for p in sorted(files)}
def hex_image(p):
    memory={};base=0;ended=False
    for line in p.read_text().splitlines():
        if ended or not line.startswith(':'):raise ValueError('Invalid HEX framing')
        data=bytes.fromhex(line[1:]);n=data[0];a=int.from_bytes(data[1:3],'big');kind=data[3]
        if len(data)!=n+5 or sum(data)&255:raise ValueError('HEX checksum/length')
        if kind==0:
            for offset,b in enumerate(data[4:-1],base+a):
                if offset in memory:raise ValueError('HEX overlap')
                memory[offset]=b
        elif kind==1:ended=True
        elif kind==4:base=int.from_bytes(data[4:-1],'big')<<16
        elif kind==5:pass
        else:raise ValueError('Unexpected HEX record type')
    if not ended:raise ValueError('HEX missing EOF')
    return memory

def elf_image(p):
    data=p.read_bytes()
    if data[:6]!=b'\x7fELF\x01\x01' or struct.unpack_from('<H',data,18)[0]!=40:raise ValueError('Expected ARM ELF32 little-endian')
    phoff=struct.unpack_from('<I',data,28)[0];shoff=struct.unpack_from('<I',data,32)[0]
    phsize,phcount=struct.unpack_from('<HH',data,42);shsize,shcount=struct.unpack_from('<HH',data,46)
    if phsize!=32 or shsize!=40:raise ValueError('ELF header sizes')
    segments=[struct.unpack_from('<8I',data,phoff+i*phsize) for i in range(phcount)]
    sections=[struct.unpack_from('<10I',data,shoff+i*shsize) for i in range(shcount)]
    image={};symbols={};ram=0
    for seg in segments:
        if seg[0]==1 and seg[4] and not (0x08000000<=seg[3]<seg[3]+seg[4]<=0x08010000):raise ValueError('PT_LOAD outside Bank1 program Flash')
    for section in sections:
        _,kind,flags,address,offset,size,link,_,_,entrysize=section
        if flags&2 and 0x20000000<=address<0x20005000:
            if address+size>0x20005000:raise ValueError('RAM allocation outside MCU')
            ram+=size
        if flags&2 and kind!=8 and size:
            owners=[s for s in segments if s[0]==1 and s[1]<=offset and offset+size<=s[1]+s[4] and address==s[2]+offset-s[1]]
            if len(owners)!=1 or offset+size>len(data):raise ValueError('Initialized section has no unique load mapping')
            load=owners[0][3]+offset-owners[0][1]
            for a,b in enumerate(data[offset:offset+size],load):
                if a in image:raise ValueError('ELF load overlap')
                image[a]=b
        if kind==2:
            strings=sections[link];names=data[strings[4]:strings[4]+strings[5]]
            for position in range(offset,offset+size,entrysize):
                name,value,_,_,_,_=struct.unpack_from('<IIIBBH',data,position)
                symbols[names[name:].split(b'\0',1)[0].decode()]=value
    return image,symbols,ram

def validate_ram_stop(image,symbols):
    """Interpret the pinned target's tiny straight-line Thumb routine.

    This checks actual ELF instructions and RAM literal addresses, not source
    strings or a claimed section name. It is not a Cortex-M/Flash timing model.
    Any changed instruction form requires a new explicit review.
    """
    start=symbols.get('stop_from_ram',0)&~1
    lo,hi=symbols.get('_sramfunc',0),symbols.get('_eramfunc',0)
    data,end,load=(symbols.get(x,0) for x in ('_sdata','_edata','_sidata'))
    if load%4 or data%4 or end%4 or not (0x20000000<=data<=lo<=start<hi<=end<=0x20005000):raise ValueError('Stop routine/literals not in startup-copied SRAM')
    def read(address,n):
        if not lo<=address<address+n<=hi:raise ValueError('Stop instruction/literal accesses outside SRAM routine')
        return sum(image[load+address-data+i]<<(8*i) for i in range(n))
    regs={};pc=start;acr=1;trace=[]
    while pc<hi:
        ins=read(pc,2)
        if ins&0xf800==0x2000:regs[(ins>>8)&7]=ins&255
        elif ins&0xf800==0x4800:regs[(ins>>8)&7]=read(((pc+4)&~3)+(ins&255)*4,4)
        elif ins&0xf800==0x6800:
            address=regs.get((ins>>3)&7,-1)+((ins>>6)&31)*4
            if address!=0x40022000:raise ValueError('Unexpected RAM-stop read target')
            regs[ins&7]=acr
        elif ins&0xf800==0x6000:
            address=regs.get((ins>>3)&7,-1)+((ins>>6)&31)*4;value=regs.get(ins&7)
            if address==0x40022008 and value in (0x04152637,0xfafbfcfd):trace.append('key1' if value==0x04152637 else 'key2')
            elif address==0x40022000:
                if value is None or value^acr!=16:raise ValueError('RUN_PD is not the only changed ACR bit')
                trace.append('powerdown' if value&16 else 'powerup');acr=value
            else:raise ValueError('Unexpected RAM-stop write target')
        elif ins&0xffc0 in (0x4300,0x4380):
            dest=ins&7;operand=regs[(ins>>3)&7]
            regs[dest]=regs[dest]|operand if ins&0xffc0==0x4300 else regs[dest]&~operand
        elif ins==0xf3bf and read(pc+2,2) in (0x8f4f,0x8f6f):
            trace.append('dsb' if read(pc+2,2)==0x8f4f else 'isb');pc+=2
        elif ins==0xbf30:trace.append('wfi')
        elif ins==0x4770:trace.append('return');break
        else:raise ValueError('Unexpected RAM-stop instruction; review target code/calls/literals')
        pc+=2
    expected=['key1','key2','powerdown','dsb','isb','wfi','powerup','dsb','isb','return']
    if trace!=expected or acr!=1:raise ValueError('RAM-stop power-down/WFI/recovery ordering differs')
    return {'execution_address':hex(start),'copied_ram_span':[hex(lo),hex(hi)],
            'bank1_load_address':hex(load+lo-data),'bytes':hi-lo,'trace':trace,
            'no_calls_or_flash_literals':True,'scope':'Bounded actual-instruction check; not hardware timing emulation'}

def validate(directory):
    image,symbols,ram=elf_image(directory/(STEM+'.elf'))
    if image!=hex_image(directory/(STEM+'.hex')):raise ValueError('ELF/HEX mismatch')
    if not image or any(not 0x08000000<=a<0x08010000 for a in image):raise ValueError('Application load outside Flash Bank1')
    binary=(directory/(STEM+'.bin')).read_bytes()
    if len(binary)!=max(image)-0x08000000+1:raise ValueError('BIN extent mismatch')
    for i,b in enumerate(binary):
        if b!=image.get(0x08000000+i,0):raise ValueError('ELF/BIN mismatch')
    def word(a):return sum(image.get(a+i,0)<<(8*i) for i in range(4))
    if word(0x08000000)!=0x20005000:raise ValueError('Initial stack pointer')
    vectors={'Reset_Handler':1,'SysTick_Handler':15,'EXTI0_1_IRQHandler':21,'SPI2_IRQHandler':42}
    for name,index in vectors.items():
        value=word(0x08000000+index*4)
        if value!=symbols.get(name) or not value&1 or (value&~1) not in image:raise ValueError('Incorrect Thumb vector '+name)
    if ram>16384:raise ValueError('Less than4KiB stack reserve')
    return {'load_bytes':len(image),'bin_bytes':len(binary),'static_ram_bytes':ram,'elf_hex_bin_equal':True,
            'bank1_only':True,'all_eeprom_excluded':True,'option_bytes_excluded':True,
            'vectors':{n:hex(symbols[n]) for n in vectors},'stop_ram_workaround':validate_ram_stop(image,symbols),'hardware_executed':False,'manufacturing_released':False}

def verify_manifest(directory=None):
    directory=directory or SOURCE/'build';m=json.loads((directory/'build-manifest.json').read_text())
    if m['schema']!=1 or m['inputs']!=inputs():raise ValueError('Source manifest changed')
    if set(m['outputs'])!=set(OUTPUTS):raise ValueError('Unexpected output set')
    for name,r in m['outputs'].items():
        if record(directory/name)!=r:raise ValueError('Build output changed: '+name)
    if validate(directory)!=m['validation']:raise ValueError('Target validation changed')
    return m

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--toolchain',type=Path);p.add_argument('--output',type=Path,default=SOURCE/'build');p.add_argument('--verify-only',action='store_true');p.add_argument('--package-url',default='https://developer.arm.com/-/media/Files/downloads/gnu/14.3.rel1/binrel/arm-gnu-toolchain-14.3.rel1-x86_64-arm-none-eabi.tar.xz');p.add_argument('--archive-sha256',default='8f6903f8ceb084d9227b9ef991490413014d991874a1e34074443c2a72b14dbd')
    a=p.parse_args();output=a.output.resolve()
    if ROOT in output.parents and SOURCE not in output.parents:p.error('Repository output must be in firmware/q5-stm32')
    if a.verify_only:verify_manifest(output);print('PASS: Q5 source/output hashes and target ELF/HEX/BIN/vector/load checks');return
    if not a.toolchain:p.error('--toolchain required')
    tc=a.toolchain.resolve();tool={n:tc/'bin'/('arm-none-eabi-'+n) for n in ('gcc','objcopy','objdump','size')}
    version=subprocess.check_output([str(tool['gcc']),'--version'],text=True).splitlines()[0]
    if '14.3.1 20250623' not in version:p.error('Pinned Arm GNU14.3.Rel1 compiler required')
    upstream=json.loads((SOURCE/'source-records.json').read_text())
    for name,expected in upstream['files'].items():
        if record(SOURCE/'vendor'/name)!=expected:raise ValueError('Pinned vendor header/license changed: '+name)
    snapshot=inputs();commands=[]
    with tempfile.TemporaryDirectory(prefix='count-fidget-q5-build-') as temporary:
        stage=Path(temporary)
        for name in snapshot:
            if name.startswith('firmware/q5-stm32/'):
                relative=Path(name).relative_to('firmware/q5-stm32');dest=stage/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
        def portable(text):return text.replace(str(stage),'<BUILD>').replace(str(tc),'<TOOLCHAIN>')
        def run(command):
            commands.append([portable(str(x)) for x in command]);return subprocess.check_output([str(x) for x in command],cwd=stage,text=True)
        flags=list(FLAGS)+['-ffile-prefix-map='+str(stage)+'=.', '-Ivendor/st','-Ivendor/arm']
        for name in SOURCES:run([tool['gcc'],*flags,'-MD','-MF',name+'.d','-c',name,'-o',name+'.o'])
        run([tool['gcc'],*flags,'-nostdlib','-T','linker.ld',*(name+'.o' for name in SOURCES),'-Wl,--gc-sections,-Map,'+STEM+'.map','-lgcc','-o',STEM+'.elf'])
        for fmt,suffix in (('ihex','.hex'),('binary','.bin')):run([tool['objcopy'],'-O',fmt,STEM+'.elf',STEM+suffix])
        (stage/(STEM+'.lst')).write_text(portable(run([tool['objdump'],'-d',STEM+'.elf'])))
        mp=stage/(STEM+'.map');mp.write_text(portable(mp.read_text()))
        (stage/'stack-usage.txt').write_text(''.join(x.read_text() for x in sorted(stage.glob('*.su'))))
        (stage/'host-tests.json').write_text(json.dumps(run_tests(),sort_keys=True,indent=2)+'\n')
        dependencies={}
        for name in SOURCES:
            content=(stage/(name+'.d')).read_text().replace('\\\n',' ')
            for item in re.findall(r'(?:\\.|[^\s])+',content.split(':',1)[1]):
                path=Path(item.replace('\\ ',' '));path=path if path.is_absolute() else stage/path
                dependencies[portable(str(path))]=record(path)
        library=Path(run([tool['gcc'],'-mcpu=cortex-m0plus','-mthumb','-print-libgcc-file-name']).strip())
        dependencies[portable(str(library))]=record(library)
        for subtool in ('cc1','as','collect2','ld'):
            executable=Path(run([tool['gcc'],'-print-prog-name='+subtool]).strip())
            dependencies[portable(str(executable))]=record(executable)
        size=run([tool['size'],STEM+'.elf']).strip();validation=validate(stage)
        if inputs()!=snapshot:raise ValueError('Source changed during build')
        m={'schema':1,'status':'Q5 engineering target; physical qualification pending','target':'STM32L072CBT6','storage':'FM25V02A-GTR SPI1 FRAM','power':'U7 soft latch on PB2; auto power-off on battery','display':'HS96L01W4S03 / SSD1315 SPI2','inputs':snapshot,'outputs':{n:record(stage/n) for n in OUTPUTS},'validation':validation,'dependencies':dependencies,'commands':commands,'size':size,'compiler':{'version':version,'tools':{n:record(t) for n,t in tool.items()},'package_url':a.package_url,'archive_sha256':a.archive_sha256}}
        (stage/'build-manifest.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n');output.mkdir(parents=True,exist_ok=True)
        for name in (*OUTPUTS,'build-manifest.json'):shutil.copyfile(stage/name,output/name)
    verify_manifest(output);print(size);print('PASS: Q5 target compiled, host fault models passed, Bank1-only ELF/HEX/BIN verified')
if __name__=='__main__':main()
