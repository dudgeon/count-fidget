"""Deterministic, explicitly conditional Q4 circuit bounds; no device simulation."""
import ast
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

def calculate(upper=150000.0, lower=49900.0, memory_c_min=6.8e-6, memory_r=68.0):
    # Independent corners are deliberately stacked, not assumed correlated.
    rerr = .001 + 25e-6*65  # 0.1%,25ppm/K,25C to-40C
    rails=[]
    # TLV767 adjustable reference +/-1%, plus precision-divider drift and
    # conservatively signed50nA bias. Extra line/load allowance is deliberately
    # stacked despite the broad accuracy row. The line test itself starts at
    # VOUT+1.5V: using its slope below that headroom is an engineering envelope,
    # NOT a manufacturer's guaranteed dropout-region characteristic.
    for ref,rt,rb,bias,line,load in itertools.product((.792,.808),(-rerr,rerr),
            (-rerr,rerr),(-50e-9,50e-9),(-.00036,.00036),(-.0001,.0001)):
        ru=upper*(1+rt); rl=lower*(1+rb)
        rails.append((ref*(1+ru/rl)+bias*ru)*(1+line+load))
    rlo=memory_r*(1-.01-100e-6*65)
    rhi=memory_r*(1+.01+100e-6*65)
    # 3mA is a declared total-current envelope, including below-minimum supply.
    # It is NOT a manufacturer-guaranteed undervoltage current characteristic.
    fall_slope=(3.3/rlo+.003)/memory_c_min
    rise_slope=(3.3/rlo)/memory_c_min
    dc_drop=.00027*rhi
    c_upstream_max=(10+2.2)*1e-6*1.1*1.15
    tmax=c_upstream_max*4.2*3.333/(math.e*.4)
    cs_tau=100000*1.01*100e-12
    cs_final_min=2.0-1e-6*101000
    cs_v100=cs_final_min*(1-math.exp(-100e-6/cs_tau))
    adc_error_terms={'factory_supply':.01/2.99,'factory_reference':.005/1.202,
        'temperature_65C':100e-6*65,'aging_1000h':.001,'line_0p3V':.002*.3,
        'adc_tue_and_quantization':4.5/(1.202/3.3*4095)}
    adc_error=sum(adc_error_terms.values())
    return {'rail_corner_cases':len(rails),'vlogic_nominal_v':.8*(1+upper/lower),
        'vlogic_min_before_transients_v':min(rails),'vlogic_max_before_transients_v':max(rails),
        'feedback_current_nominal_uA':.8/lower*1e6,
        'lowest_adc_estimate_on_regulated_corner_v':min(rails)*.98,
        'display_enable_margin_at_regulated_corner_mv':(min(rails)*.98-3.08)*1000,
        'regulator_iq_typ_uA':50,'regulator_iq_max_uA':80,
        'regulator_alone_cell45mAh_ideal_days_at_max_iq_and_divider':45/(.080+.8/lower*1000)/24,
        'memory_r_min_ohm':rlo,'memory_r_max_ohm':rhi,
        'memory_c_effective_min_uF':memory_c_min*1e6,
        'memory_rise_min_us_per_v':1e6/rise_slope,'memory_fall_min_us_per_v':1e6/fall_slope,
        'memory_active_dc_drop_max_v':dc_drop,
        'memory_miso_margin_at_pvd5_min_v':2.77-dc_drop-.2-.7*2.77,
        'cs_100us_voltage_at_vfram2_v':cs_v100,'cs_required_vih_at_vfram2_v':1.4,
        'upstream_c_max_uF':c_upstream_max*1e6,'upstream_scc_exposure_max_us':tmax*1e6,
        'usb_first_c3_max_uF':2.2*1.1*1.15,
        'usb_first_scc_exposure_max_us':2.2e-6*1.1*1.15*4.2*3.333/(math.e*.4)*1e6,
        'bat_sense_branch_max_mA':4.2/(330*.99)*1000,
        'usb_first_with_sense_branch_scc_exposure_max_us':2.2e-6*1.1*1.15*4.2*3.333/(math.e*(.4-4.2/(330*.99)*3.333))*1e6,
        'scc_min_delay_us':125,'cold_insertion_bound_passes':tmax<125e-6,
        'adc_error_terms_fraction':adc_error_terms,'adc_stacked_error_fraction':adc_error,
        'adc_budget_fraction':.02,'oled_off_estimate_mv':3070,'oled_on_estimate_mv':3080,
        'oled_off_actual_min_v_before_latency_drop':3.07/1.02,
        'oled_off_actual_min_v_after_15mA_175mohm_switch_envelope':3.07/1.02-.015*.175}

def validate_model():
    p=ROOT/'scripts/build_q4_model.py'
    ast.parse(p.read_text())
    import importlib.util
    spec=importlib.util.spec_from_file_location('q4model',p); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    m=mod.make_model(); parts={p['ref']:p for p in m['parts']}
    assert len(parts)==len(m['parts'])
    assert m['board_mm']==[42,54,1] and m['layers']==2
    assert not m['hardware_tested'] and not m['manufacturing_released']
    assert m['source_baseline_sha256']==hashlib.sha256((ROOT/'electronics/q3/netlist-Q3.json').read_bytes()).hexdigest()
    assert len(m['symbol_pins']['U1'])==48
    for p in parts.values():
        if p['ref'] in m['symbol_pins']:
            assert set(p['pins'])<=set(m['symbol_pins'][p['ref']])
    assert parts['U1']['pins']['44']==parts['U1']['pins']['11']=='BOOT_COUNT_RESET'
    assert parts['SW3']['pins']=={'1':'NRST','2':'GND'}
    assert parts['U6']['pins']=={'1':'VLOGIC','2':'GND','3':'OLED_ENABLE','4':'OLED_CT','5':'OLED_SUPPLY','6':'OLED_SUPPLY'}
    assert parts['U7']['pins']=={'1':'SYS','2':'GND','3':'SYS','4':'SYS_CT','6':'SYS_LOAD'}
    assert parts['C28']['pins']=={'1':'VLOGIC','2':'OLED_CT'}
    assert parts['C29']['pins']=={'1':'SYS','2':'SYS_CT'}
    assert parts['R32']['pins']=={'1':'VLOGIC','2':'VFRAM'}
    assert parts['U8']['mpn']=='FM25V02A-GTR'
    assert parts['U3']['mpn']=='TLV76701DRVR'
    assert parts['R30']['mpn']=='RT0603BRD07150KL'
    assert parts['R31']['mpn']=='RT0603BRD0749K9L'
    contract=json.loads((ROOT/'electronics/q4/circuit-contract.json').read_text())
    for group in ('parts','critical_controls'):
        for ref, required in contract[group].items():
            actual=parts[ref]
            for field in ('mpn','value','pins'):
                if field in required: assert actual[field]==required[field], (ref,field)
            if 'nc' in required and ref in m['symbol_pins']:
                assert set(required['nc'])==set(m['symbol_pins'][ref])-set(actual['pins']),ref
    assert all(parts[r]['assembly']=='home_through_hole' for r in ('DS1','SW1','SW2'))
    assert parts['R33']['pins']=={'1':'VFRAM','2':'FRAM_CS_N'}
    assert all(p['footprint'].startswith('CountFidgetQ4:') for p in parts.values())
    assert not any(n.startswith(('LCD_','OLED_C1','OLED_C2','OLED_VBAT','LX')) for p in parts.values() for n in p['pins'].values())
    # Preserve the reviewed push-pull comparator circuit exactly.
    baseline={p['ref']:p for p in json.loads((ROOT/'electronics/q3/netlist-Q3.json').read_text())['parts']}
    for ref in ('U5','Q3','Q4','R10','R11','R12','R13','R14','R15'):
        assert parts[ref]['pins']==baseline[ref]['pins']
    assert parts['U5']['mpn']=='TLV7012DGKR'
    return {'references':len(parts),'fitted':m['fitted_components'],'full_mcu_pins':48,
        'circuit_contract_checks':'PASS; native footprint/ERC/routing validation separate'}

if __name__=='__main__':
    result=calculate()
    assert result['vlogic_min_before_transients_v']>3
    assert result['vlogic_max_before_transients_v']<3.3
    assert result['lowest_adc_estimate_on_regulated_corner_v']>3.08
    assert result['usb_first_with_sense_branch_scc_exposure_max_us']<125
    assert result['memory_rise_min_us_per_v']>50
    assert result['memory_fall_min_us_per_v']>100
    assert result['memory_miso_margin_at_pvd5_min_v']>.5
    assert result['cs_100us_voltage_at_vfram2_v']>1.4
    assert result['adc_stacked_error_fraction']<.02
    assert not result['cold_insertion_bound_passes']
    # Meaningful counterexamples: inadequate C fails ramp; high divider fails rail.
    assert calculate(memory_c_min=1e-6)['memory_fall_min_us_per_v']<100
    assert calculate(upper=160000)['vlogic_max_before_transients_v']>3.3
    # Original higher-resistance3.2V divider cannot guarantee the selectedADCgate.
    assert calculate(upper=300000,lower=100000)['lowest_adc_estimate_on_regulated_corner_v']<3.08
    report={'status':'CONDITIONAL ANALYTICAL CHECKS PASS; HARDWARE NOT QUALIFIED',
        'coverage':'Linear RC/current envelopes and stacked data-sheet corners, not SPICE or a whole-board simulator.',
        'limitations':['No verified below-2V FRAM current model;3mA all-voltage bound is a test condition.',
        'Effective MLCC capacitance>=6.8uF requires vendor curve or measurement at bias/temperature/aging.',
        'TLV767 line-regulation test is atVOUT+1.5V or higher; the added slope allowance below that headroom is conditional, not a low-headroom guarantee.',
        'TLV767 accuracy row starts at1mA; very-light-load accuracy, dropout/overshoot,reverse current and complete module capacitance remain unverified.',
        'Module switch voltage loss, ADC sampling latency, abrupt supply collapse and USB signal integrity are not simulated.',
        'Charger/protector recovery state machines and real cell impedance are not simulated.',
        'USB-first commissioning is a testable proposed service workflow, not a validated recovery guarantee.'],
        'model_checks':validate_model(),'results':result,'negative_checks':3,
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (Path(__file__),ROOT/'scripts/build_q4_model.py',ROOT/'electronics/q4/netlist-Q4.json',ROOT/'electronics/q4/circuit-contract.json')}}
    (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
