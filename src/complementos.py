from pathlib import Path
import sys

from analisis import *
from sklearn.metrics import adjusted_rand_score
D=cargar();parts=pd.read_csv(OUT/'particiones.csv');tr=parts.loc[parts.particion.eq('train'),'fila'].to_numpy();te=parts.loc[parts.particion.eq('test'),'fila'].to_numpy()
# Sensibilidad de perfiles incorporando desfase, solicitada por la guia.
cols=NUM[:0]+['rural','electricidad','internet_hogar','uso_internet','frecuencia_tic','log_ingreso_pc','log_gasto_pc','miembros_hogar','ratio_alumno_docente','proporcion_publica','anios_desfase']
p=Pipeline([('imputar',SimpleImputer(strategy='median')),('escalar',StandardScaler())]);A=p.fit_transform(D.iloc[tr][cols]);B=p.transform(D.iloc[te][cols]);rows=[];mods={};rng=np.random.default_rng(42);sample=rng.choice(len(A),1800,replace=False)
for alg in ['KMeans','GMM']:
 for k in range(2,7):
  m=KMeans(n_clusters=k,n_init=10,random_state=42) if alg=='KMeans' else GaussianMixture(n_components=k,n_init=2,reg_covar=1e-4,random_state=42)
  m.fit(A);lab=m.predict(A[sample]);mods[(alg,k)]=m;rows.append({'algoritmo':alg,'k':k,'silueta':silhouette_score(A[sample],lab),'Davies_Bouldin':davies_bouldin_score(A[sample],lab),'Calinski_Harabasz':calinski_harabasz_score(A[sample],lab)})
s=pd.DataFrame(rows).sort_values('silueta',ascending=False);s.to_csv(OUT/'sensibilidad_clustering_con_desfase.csv',index=False)
w=s.iloc[0];m=mods[(w.algoritmo,int(w.k))];lab=np.empty(len(D),int);lab[tr]=m.predict(A);lab[te]=m.predict(B)
base=pd.read_csv(OUT/'asignacion_clusters.csv').cluster.to_numpy();dump('sensibilidad_clustering',{'ganador':w.to_dict(),'ARI_con_perfiles_recursos_train':adjusted_rand_score(base[tr],lab[tr]),'nota':'Perfil alternativo incluye desfase para cubrir la variable sugerida por la guia; sus diferencias de rezago son parcialmente definitorias. No se usa en el clasificador.'})
# Inferencia descriptiva agrupada del contraste de acumulacion.
q=json.loads((OUT/'resumen_desventaja.json').read_text(encoding='utf8'))['umbral_ratio_train_P75'];a=D.iloc[te].dropna(subset=['internet_hogar','ratio_alumno_docente']).copy();a['grupo']=a.internet_hogar.eq(0).astype(int)*2+a.ratio_alumno_docente.ge(q).astype(int)
mat=a.groupby(['conglome','grupo']).rezago.agg(['sum','count']).unstack(fill_value=0).reindex(columns=pd.MultiIndex.from_product([['sum','count'],range(4)]),fill_value=0)
boots=[];rng=np.random.default_rng(42)
for _ in range(1000):
 b=mat.iloc[rng.integers(0,len(mat),len(mat))].sum();rate=b['sum']/b['count']
 if np.isfinite(rate).all():boots.append(float(rate[3]-rate[2]-rate[1]+rate[0]))
obj=json.loads((OUT/'resumen_desventaja.json').read_text(encoding='utf8'));obj['IC95_contraste_bootstrap_conglomerados']=np.quantile(boots,[.025,.975]).tolist();obj['replicas_validas']=len(boots);dump('resumen_desventaja',obj)
print(json.dumps(obj,indent=2))
# Diagrama relacional para documentar cardinalidades.
from matplotlib.patches import FancyBboxPatch
fig,ax=plt.subplots(figsize=(10,3));ax.set(xlim=(0,10),ylim=(0,3));ax.axis('off')
boxes=[(.1,1.9,'200 Personas\n6 a 17 años'),(.1,.6,'300 Educación\nPersona 1:1'),(3.1,1.9,'100 Vivienda\nHogar N:1'),(3.1,.6,'Sumaria\nHogar N:1'),(6.4,1.5,'Maestro analítico\n19 286 estudiantes'),(6.4,.1,'Padrón + Padlocal\nDistrito y área N:1')]
for x,y,t in boxes:
 ax.add_patch(FancyBboxPatch((x,y),2.5,.65,boxstyle='round,pad=0.05',fc='#EDF4F6',ec='#176B87'));ax.text(x+1.25,y+.325,t,ha='center',va='center',fontsize=10)
for start,end in [((2.6,2.2),(6.3,1.85)),((2.6,.9),(6.3,1.75)),((5.6,2.2),(6.3,1.95)),((5.6,.9),(6.3,1.65)),((7.65,.8),(7.65,1.45))]:ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':'#52666F'})
guardar('diagrama_cruces')

