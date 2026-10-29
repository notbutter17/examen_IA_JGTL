from pathlib import Path
import json, zipfile, tempfile
import numpy as np
import pandas as pd
from dbfread import DBF

ROOT = Path(__file__).resolve().parents[1]
RAW, DATA, OUT = ROOT/'data/raw', ROOT/'data/processed', ROOT/'resultados'
HH = ['conglome','vivienda','hogar']
PK = HH+['codperso']
def numero(s): return pd.to_numeric(s, errors='coerce')
def binaria(s): return s.map({'1':1.,'2':0.})

def leer(mod):
    d = pd.read_csv(RAW/f'modulo_{mod}_2025.csv',dtype=str,encoding='utf-8-sig')
    for c,n in [('conglome',6),('vivienda',3),('hogar',2),('codperso',2),('ubigeo',6)]:
        if c in d: d[c] = d[c].str.strip().str.zfill(n)
    keys = PK if 'codperso' in d else HH
    assert not d.duplicated(keys).any(), f'Llaves repetidas en {mod}'
    return d

def dbf_zip(nombre, columnas):
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(RAW/nombre) as z:
            fn=next(n for n in z.namelist() if n.lower().endswith('.dbf'))
            p=Path(tmp)/Path(fn).name; p.write_bytes(z.read(fn))
        return pd.DataFrame([{c:r.get(c) for c in columnas} for r in DBF(str(p),encoding='latin1',char_decode_errors='replace')])

def contexto():
    p = dbf_zip('00_Padron.zip',['COD_MOD','ANEXO','CODLOCAL','CODGEO','AREA_CENSO','NIV_MOD','GESTION','ESTADO','TALUM','TDOC','NLAT_IE','NLONG_IE','FECHA_ACT'])
    l = dbf_zip('00_Padlocal.zip',['CODLOCAL','CODGEO','ESTADO'])
    assert not l.CODLOCAL.duplicated().any()
    p=p.loc[p.ESTADO.eq('1') & p.NIV_MOD.isin(['B0','F0'])].copy()
    assert not p.duplicated(['COD_MOD','ANEXO']).any()
    p=p.merge(l[['CODLOCAL','CODGEO']].rename(columns={'CODGEO':'geo_local'}),on='CODLOCAL',how='left',validate='many_to_one')
    for c in ['TALUM','TDOC','NLAT_IE','NLONG_IE']: p[c]=numero(p[c])
    p['ubigeo']=p.CODGEO.str.zfill(6)
    p['rural']=p.AREA_CENSO.map({'1':0.,'2':1.})
    p['publico']=p.GESTION.isin(['1','2']).astype(float)
    p['latitud']=p.NLAT_IE.where(p.NLAT_IE.between(-19,1))
    p['longitud']=p.NLONG_IE.where(p.NLONG_IE.between(-82,-68))
    valido=p.TALUM.ge(0) & p.TDOC.gt(0)
    p['alumnos_validos']=p.TALUM.where(valido);p['docentes_validos']=p.TDOC.where(valido)
    g=p.groupby(['ubigeo','rural'],dropna=False).agg(escuelas=('COD_MOD','size'),proporcion_publica=('publico','mean'),
        alumnos=('alumnos_validos',lambda s:s.sum(min_count=1)),docentes=('docentes_validos',lambda s:s.sum(min_count=1)),
        latitud=('latitud','mean'),longitud=('longitud','mean'),servicios_con_conteos=('docentes_validos','count')).reset_index()
    g['ratio_alumno_docente']=g.alumnos/g.docentes
    g.to_csv(DATA/'contexto_distrito_area.csv',index=False)
    meta={'servicios_primaria_secundaria_activos':len(p),'locales_vinculados':int(p.geo_local.notna().sum()),
          'geocodigos_discrepantes':int((p.geo_local.notna() & p.geo_local.ne(p.CODGEO)).sum()),
          'fechas_padron':p.FECHA_ACT.value_counts().head(5).to_dict(),
          'altitud':'No disponible en Padron ni Padlocal suministrados; no se fabrica.',
          'unidad':'Servicios activos B0/F0; contexto del distrito y area, no escuela de cada estudiante.'}
    return g,meta

def construir():
    DATA.mkdir(parents=True,exist_ok=True);OUT.mkdir(exist_ok=True)
    personas,edu,hogar,suma=leer(1479),leer(1475),leer(1474),leer(1478)
    flujo=[{'etapa':'Personas con identificacion 2025','n':len(personas)}]
    edad=numero(personas.p208a)
    personas=personas.loc[edad.between(6,17)].copy();flujo.append({'etapa':'Edad de 6 a 17 anos','n':len(personas)})
    residentes=(personas.p204.eq('1') & personas.p205.eq('2')) | (personas.p204.eq('2') & personas.p206.eq('1'))
    personas=personas.loc[residentes].copy();flujo.append({'etapa':'Residentes habituales','n':len(personas)})
    d=personas.merge(edu,on=PK,how='left',validate='one_to_one',indicator='cruce_educacion')
    d=d.merge(hogar.drop(columns=['ubigeo']),on=HH,how='left',validate='many_to_one',indicator='cruce_hogar')
    d=d.merge(suma.rename(columns={'factor07':'factor07_sumaria'}),on=HH,how='left',validate='many_to_one',indicator='cruce_sumaria')
    nivel=numero(d.p308a);grado_prim=numero(d.p308c);anio_sec=numero(d.p308b)
    grado=pd.Series(np.nan,index=d.index)
    grado.loc[nivel.eq(2) & grado_prim.between(1,6)]=grado_prim
    grado.loc[nivel.eq(3) & anio_sec.between(1,5)]=anio_sec+6
    valido=d.p306.eq('1') & grado.notna()
    d=d.loc[valido].copy(); grado=grado.loc[valido]
    flujo.append({'etapa':'Matriculados primaria/secundaria con grado valido','n':len(d)})
    a=pd.DataFrame(index=d.index)
    for c in PK+['ubigeo']:a[c]=d[c]
    a['edad']=numero(d.p208a);a['grado_acumulado']=grado;a['edad_normativa']=grado+5
    a['anios_desfase']=(a.edad-a.edad_normativa).clip(lower=0)
    a['rezago']=a.anios_desfase.gt(0).astype(int);a['atraso_dos_anios']=a.anios_desfase.ge(2).astype(int)
    a['mujer']=d.p207.map({'1':0.,'2':1.})
    estrato=numero(d.estrato)
    a['rural']=pd.Series(np.nan,index=d.index).mask(estrato.between(1,5),0.).mask(estrato.between(6,8),1.)
    a['lengua']=d.p300a.fillna('Sin respuesta')
    a['lengua_originaria']=d.p300a.map(lambda x:np.nan if pd.isna(x) or x in ['8','9'] else float(x not in ['4','6','7']))
    a['dominio']=d.dominio.fillna('Sin respuesta')
    # P1121/P1144 son seleccion multiple 0=pase/no seleccionado y 1=seleccionado; P314A usa 1/2.
    a['electricidad']=d.p1121.map({'0':0.,'1':1.});a['internet_hogar']=d.p1144.map({'0':0.,'1':1.});a['uso_internet']=binaria(d.p314a)
    a['frecuencia_tic']=d.p314d.map({'1':3.,'2':2.,'3':1.,'4':0.5});a.loc[d.p314a.eq('2'),'frecuencia_tic']=0.
    a['pobreza']=d.pobreza.fillna('Sin respuesta')
    miembros=numero(d.mieperho).where(numero(d.mieperho).gt(0));a['miembros_hogar']=miembros
    a['ingreso_pc_mensual']=numero(d.inghog2d).where(numero(d.inghog2d).ge(0))/miembros/12
    a['gasto_pc_mensual']=numero(d.gashog2d).where(numero(d.gashog2d).ge(0))/miembros/12
    a['log_ingreso_pc']=np.log1p(a.ingreso_pc_mensual);a['log_gasto_pc']=np.log1p(a.gasto_pc_mensual)
    a['FACTOR07']=numero(d.factor07_sumaria).where(numero(d.factor07_sumaria).gt(0));a['FACPOB07']=numero(d.facpob07).where(numero(d.facpob07).gt(0))
    ctx,meta=contexto();a=a.merge(ctx,on=['ubigeo','rural'],how='left',validate='many_to_one',indicator='cruce_escale')
    a['contexto_encontrado']=a.cruce_escale.eq('both').astype(int);a=a.drop(columns='cruce_escale').reset_index(drop=True)
    assert not a.duplicated(PK).any()
    a.to_csv(DATA/'dataset_enaho_escale_2025.csv',index=False,encoding='utf-8-sig');a.to_parquet(DATA/'dataset_enaho_escale_2025.parquet',index=False)
    pd.DataFrame(flujo).to_csv(OUT/'flujo_poblacion.csv',index=False);a.isna().mean().rename('proporcion_faltante').to_csv(OUT/'faltantes.csv')
    meta.update({'filas':len(a),'columnas':len(a.columns),'conglomerados':int(a.conglome.nunique()),'distritos':int(a.ubigeo.nunique()),
        'cobertura_contexto':a.contexto_encontrado.mean(),'prevalencia_rezago':a.rezago.mean(),'prevalencia_atraso_dos_anios':a.atraso_dos_anios.mean(),
        'fechas_nacimiento_disponibles':int(d[['p208b1','p208c1','p208d1']].notna().all(axis=1).sum()),
        'cruces':{c:d[c].value_counts().to_dict() for c in ['cruce_educacion','cruce_hogar','cruce_sumaria']}})
    (OUT/'auditoria_datos.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False),encoding='utf8');print(json.dumps(meta,ensure_ascii=False,indent=2),flush=True)
    return a
if __name__=='__main__': construir()

