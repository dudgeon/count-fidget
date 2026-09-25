"""Compile/run the production Q4 portable code against deterministic fault models."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'firmware/q4-stm32'
GROUPS={'behavior':['test_behavior.c','counter.c','input.c','journal.c','app.c'],
        'fram':['test_fram.c','fram.c','journal.c'],
        'oled':['test_oled.c','oled.c'],'rail':['test_rail.c','rail.c']}
def record(p):
    data=p.read_bytes();return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def run_tests(sanitize=False):
    outputs={}
    source_files=[p for p in SOURCE.glob('*') if p.suffix in ('.c','.h')]
    before={p.name:record(p) for p in source_files}
    with tempfile.TemporaryDirectory(prefix='count-fidget-q4-tests-') as td:
        for name,files in GROUPS.items():
            exe=Path(td)/name
            command=['clang','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(SOURCE)]
            if sanitize:command+=['-fsanitize=undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-DTEAR_STEP=257']
            subprocess.run(command+[str(SOURCE/f) for f in files]+['-o',str(exe)],check=True,capture_output=True,text=True)
            outputs[name]=subprocess.check_output([str(exe)],text=True,timeout=180)
    if before!={p.name:record(p) for p in source_files}:raise ValueError('Source changed during test run')
    return outputs

def image_checks(directory):
    from build_firmware_q4 import validate,verify_manifest,hex_image,elf_image,validate_ram_stop,STEM,OUTPUTS
    baseline=verify_manifest(directory);rejections=[]
    with tempfile.TemporaryDirectory(prefix='q4-image-negative-') as td:
        out=Path(td)
        def reset():
            for name in (*OUTPUTS,'build-manifest.json'):shutil.copyfile(directory/name,out/name)
        def rejected(name,check=validate):
            try:check(out)
            except (ValueError,KeyError):rejections.append(name)
            else:raise AssertionError('Corruption falsely accepted: '+name)
        reset();p=out/(STEM+'.bin');data=bytearray(p.read_bytes());data[-1]^=1;p.write_bytes(data);rejected('BIN payload changed')
        reset();p=out/(STEM+'.elf');data=bytearray(p.read_bytes());struct.pack_into('<H',data,18,105);p.write_bytes(data);rejected('Wrong MCU ELF architecture')
        reset();p=out/(STEM+'.elf');data=bytearray(p.read_bytes());phoff=struct.unpack_from('<I',data,28)[0];struct.pack_into('<I',data,phoff+12,0x08080c00);p.write_bytes(data);rejected('EEPROM PT_LOAD introduced')
        reset();p=out/(STEM+'.elf');data=bytearray(p.read_bytes());phoff=struct.unpack_from('<I',data,28)[0];struct.pack_into('<I',data,phoff+12,0x08010000);p.write_bytes(data);rejected('Code moved to Flash Bank2')
        reset();p=out/(STEM+'.elf');data=bytearray(p.read_bytes());phoff=struct.unpack_from('<I',data,28)[0];offset=struct.unpack_from('<I',data,phoff+4)[0];struct.pack_into('<I',data,offset+4,0);p.write_bytes(data)
        p=out/(STEM+'.bin');data=bytearray(p.read_bytes());data[4:8]=bytes(4);p.write_bytes(data)
        p=out/(STEM+'.hex');memory=hex_image(p)
        for a in range(0x08000004,0x08000008):memory[a]=0
        def line(kind,a,payload):
            b=bytes([len(payload),a>>8,a&255,kind])+payload;return ':'+(b+bytes([-sum(b)&255])).hex().upper()
        lines=[line(4,0,bytes([8,0]))];addresses=sorted(memory);index=0
        while index<len(addresses):
            a=addresses[index];chunk=[memory[a]];index+=1
            while index<len(addresses) and addresses[index]==a+len(chunk) and len(chunk)<16:chunk.append(memory[addresses[index]]);index+=1
            lines.append(line(0,a&65535,bytes(chunk)))
        lines.append(line(1,0,b''));p.write_text('\n'.join(lines)+'\n');rejected('Reset vector removed consistently from ELF HEX BIN')
        reset();p=out/'build-manifest.json';m=json.loads(p.read_text());m['inputs'][next(iter(m['inputs']))]['sha256']='0'*64;p.write_text(json.dumps(m));rejected('Source manifest tampered',verify_manifest)
    image,symbols,_=elf_image(directory/(STEM+'.elf'))
    start=symbols['stop_from_ram']&~1;load=symbols['_sidata']+start-symbols['_sdata']
    for name,offset,payload,changed_symbol in [
        ('RAM Stop WFI removed',26,bytes.fromhex('00bf'),None),
        ('RAM Stop RUN_PD never cleared',30,bytes.fromhex('0a43'),None),
        ('RAM Stop literal fetch escapes SRAM',2,bytes.fromhex('ff4b'),None),
        ('RAM Stop unlock key corrupted',48,bytes(4),None),
        ('Stop function linked back into Flash',None,None,('stop_from_ram',0x08000101)),
        ('Startup copy omits Stop literal pool',None,None,('_edata',start+44)),
        ('Startup copy load becomes unaligned',None,None,('_sidata',symbols['_sidata']+1)),
    ]:
        altered=dict(image);syms=dict(symbols)
        if offset is not None:
            for i,b in enumerate(payload):altered[load+offset+i]=b
        if changed_symbol:syms[changed_symbol[0]]=changed_symbol[1]
        try:validate_ram_stop(altered,syms)
        except (ValueError,KeyError):rejections.append(name)
        else:raise AssertionError('Unsafe actual-instruction corruption accepted: '+name)
    return {'passed':True,'rejected':rejections,'baseline_manifest':record(directory/'build-manifest.json'),
            'ram_stop_instruction_check':baseline['validation']['stop_ram_workaround'],'image_outputs':baseline['outputs']}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sanitize',action='store_true');p.add_argument('--output',type=Path);p.add_argument('--image-only',action='store_true');p.add_argument('--images',type=Path,default=SOURCE/'build')
    a=p.parse_args()
    if a.image_only:
        result=image_checks(a.images);print('PASS: '+str(len(result['rejected']))+' deliberately corrupted target/image-manifest cases rejected')
        if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        return
    outputs=run_tests(a.sanitize)
    result={'schema':1,'target':'STM32L072CBT6 Q4','passed':True,'sanitized':a.sanitize,'sanitizer':'UndefinedBehaviorSanitizer' if a.sanitize else None,
            'hardware_executed':False,'models':'Production portable code; memory/bus/input models, not MCU or whole-board emulation',
            'results':outputs,'inputs':{str(x.relative_to(ROOT)):record(x) for x in sorted(SOURCE.glob('*')) if x.suffix in ('.c','.h')},
            'runner':record(Path(__file__)),'host_compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0]}
    for output in outputs.values():print(output,end='')
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
