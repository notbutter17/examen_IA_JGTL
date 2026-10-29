"""Contratos sustantivos de integridad, separación y resultados."""
import json,hashlib
import numpy as np,pandas as pd
from datos import ROOT,DATA,OUT,PK
from analisis import NUM,CAT,FORBIDDEN

def verificar():
 d=pd.read_parquet(DATA/'dataset_enaho_escale_2025.parquet');s=pd.read_csv(OUT/'particiones.csv',dtype={'conglome':str});checks=[]
 def check(name,condition):
  checks.append({'prueba':name,'cumple':bool(condition)});assert condition,name
 check('Llave de persona unica',not d.duplicated(PK).any())
 check('Poblacion entre 6 y 17',d.edad.between(6,17).all())
 check('Normativa derivada correctamente',np.allclose(d.edad_normativa,d.grado_acumulado+5))
 check('Etiqueta consistente con definicion',(d.rezago.eq((d.edad>d.edad_normativa).astype(int))).all())
 check('No hay proxies directos en predictores',not (set(NUM+CAT)&FORBIDDEN))
 check('Todas las personas asignadas exactamente una vez',len(s)==len(d) and not s.fila.duplicated().any())
 tr=s.loc[s.particion.eq('train')];te=s.loc[s.particion.eq('test')]
 check('Conglomerados train test disjuntos',not set(tr.conglome)&set(te.conglome))
 for fold in range(1,6):check(f'Fold {fold} sin solapamiento',not set(tr.loc[tr.fold_validacion.eq(fold),'conglome'])&set(tr.loc[tr.fold_validacion.ne(fold),'conglome']))
 for c in ['internet_hogar','electricidad','uso_internet']:check('Codigos binarios '+c,set(d[c].dropna().unique())<= {0,1})
 check('Internet conserva ambas categorias',set(d.internet_hogar.dropna().unique())=={0,1})
 dictionary=pd.read_csv(DATA/'diccionario_variables.csv');check('Diccionario cubre todas las columnas',set(dictionary.variable)==set(d.columns))
 cv=pd.read_csv(OUT/'comparacion_validacion.csv');m=json.loads((OUT/'resumen_modelos.json').read_text(encoding='utf8'))
 check('Ganador elegido en CV',cv.sort_values('CV_PR_AUC_AP',ascending=False).iloc[0].modelo==m['ganador'])
 check('Conteos de confusion coinciden con test',sum(map(sum,m['matriz_confusion']))==len(te))
 shap=json.loads((OUT/'resumen_shap.json').read_text(encoding='utf8'));check('Aditividad SHAP verificada',shap['error_aditividad_max']<1e-4)
 pred=pd.read_csv(OUT/'predicciones_test.csv').set_index('fila')
 for label,case in shap['casos'].items():check('Waterfall correcto '+label,int(pred.loc[case['fila'],'rezago'])==int(pred.loc[case['fila'],'prediccion']))
 for x in json.loads((ROOT/'docs/manifiesto_fuentes.json').read_text(encoding='utf8')):
  if 'sha256_seleccion' in x:
   mod=x['archivo_original'].split('Modulo')[1].split('.')[0];check('Hash seleccion '+mod,hashlib.sha256((ROOT/f'data/raw/modulo_{mod}_2025.csv').read_bytes()).hexdigest()==x['sha256_seleccion'])
 pd.DataFrame(checks).to_csv(OUT/'verificacion_integridad.csv',index=False);print(pd.DataFrame(checks).to_string(index=False));return checks
if __name__=='__main__':verificar()
