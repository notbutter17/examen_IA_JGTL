"""Extrae selecciones de 2025 sin ejecutar ni copiar codigo de otros proyectos."""
import argparse,hashlib,json,zipfile,shutil
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1]
SPEC={1474:['conglome','vivienda','hogar','ubigeo','estrato','dominio','p1121','p1144','factor07'],1479:['conglome','vivienda','hogar','codperso','ubigeo','p203','p204','p205','p206','p207','p208a','p208b1','p208c1','p208d1','facpob07'],1475:['conglome','vivienda','hogar','codperso','p300a','p306','p307','p308a','p308b','p308c','p314a','p314d'],1478:['conglome','vivienda','hogar','mieperho','inghog2d','gashog2d','pobreza','factor07']}
def extraer(folder):
    dest=R/'data/raw';dest.mkdir(parents=True,exist_ok=True);manifest=[]
    for mod,cols in SPEC.items():
        p=folder/f'1041-Modulo{mod}.zip';z=zipfile.ZipFile(p);fn=next(n for n in z.namelist() if n.lower().endswith('.csv'))
        with z.open(fn) as s:
            chunks=[]
            for chunk in pd.read_csv(s,usecols=[c+'_25' for c in cols],dtype=str,encoding='utf-8-sig',chunksize=8000,na_values=[' ','  ','   ','    ','']):
                chunk=chunk.apply(lambda c:c.str.strip().replace('',pd.NA));chunks.append(chunk.loc[chunk.conglome_25.notna()])
        d=pd.concat(chunks,ignore_index=True);d.columns=d.columns.str.removesuffix('_25');out=dest/f'modulo_{mod}_2025.csv';d.to_csv(out,index=False,encoding='utf-8-sig')
        manifest.append({'archivo_original':p.name,'miembro_csv':fn,'sha256_original':hashlib.sha256(p.read_bytes()).hexdigest(),'seleccion_columnas':list(d.columns),'filas':len(d),'sha256_seleccion':hashlib.sha256(out.read_bytes()).hexdigest(),'codificacion_verificada':'utf-8-sig'})
        print(mod,d.shape,flush=True)
    for name in ['00_Padron.zip','00_Padlocal.zip']:
        p=folder/name;shutil.copyfile(p,dest/name);manifest.append({'archivo_original':name,'sha256_original':hashlib.sha256(p.read_bytes()).hexdigest()})
    (R/'docs/manifiesto_fuentes.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf8')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--originales',type=Path,required=True,help='Carpeta con los seis ZIP originales');extraer(ap.parse_args().originales)
