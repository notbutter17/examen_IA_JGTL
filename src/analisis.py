"""Modelos agrupados y análisis de acumulación de desventajas. Semilla 42."""
from pathlib import Path
import json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import GroupShuffleSplit,GroupKFold,ParameterGrid
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, confusion_matrix, ConfusionMatrixDisplay, roc_curve, precision_recall_curve, brier_score_loss, silhouette_score, silhouette_samples, davies_bouldin_score, calinski_harabasz_score
from sklearn.calibration import calibration_curve
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.decomposition import PCA
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
import joblib
from datos import ROOT,DATA,OUT

SEED=42
FIG=OUT/'figuras';FIG.mkdir(exist_ok=True)
NUM=['mujer','rural','electricidad','internet_hogar','uso_internet','frecuencia_tic','log_ingreso_pc','log_gasto_pc','miembros_hogar','ratio_alumno_docente','proporcion_publica','latitud','longitud']
CAT=['lengua','pobreza','dominio']
FORBIDDEN={'edad','grado_acumulado','edad_normativa','anios_desfase','rezago','atraso_dos_anios','conglome','vivienda','hogar','codperso','ubigeo','FACTOR07','FACPOB07','cluster'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':120,'savefig.dpi':170})
COLORS=['#176B87','#DB7046','#658C52','#9B6588','#707070']

def guardar(nombre):
    plt.tight_layout();plt.savefig(FIG/(nombre+'.png'),bbox_inches='tight');plt.close()
def dump(nombre,obj):
    (OUT/(nombre+'.json')).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=lambda x:x.item() if isinstance(x,np.generic) else str(x)),encoding='utf8')
def prep():
    return ColumnTransformer([('num',Pipeline([('imputar',SimpleImputer(strategy='median',keep_empty_features=True)),('escalar',StandardScaler())]),NUM),('cat',Pipeline([('imputar',SimpleImputer(strategy='most_frequent')),('codificar',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),CAT)],verbose_feature_names_out=False)
def metricas(y,p,w=None):
    return {'ROC_AUC':roc_auc_score(y,p,sample_weight=w),'PR_AUC_AP':average_precision_score(y,p,sample_weight=w),'F1_macro':f1_score(y,p>=.5,average='macro',sample_weight=w,zero_division=0),'Brier':brier_score_loss(y,p,sample_weight=w)}
def cargar():
    d=pd.read_parquet(DATA/'dataset_enaho_escale_2025.parquet')
    for c in CAT:d[c]=d[c].astype(str)
    return d

def entrenar(d):
    assert not (set(NUM+CAT)&FORBIDDEN)
    X=d[NUM+CAT];y=d.rezago.to_numpy();g=d.conglome.to_numpy()
    tr,te=next(GroupShuffleSplit(test_size=.2,n_splits=1,random_state=SEED).split(X,y,g))
    assert not set(g[tr])&set(g[te])
    folds=list(GroupKFold(5).split(X.iloc[tr],y[tr],g[tr]))
    for a,b in folds: assert not set(g[tr[a]])&set(g[tr[b]])
    partition=pd.DataFrame({'fila':np.arange(len(d)),'conglome':g,'particion':np.where(np.isin(np.arange(len(d)),te),'test','train'),'fold_validacion':-1})
    for k,(a,b) in enumerate(folds):partition.loc[tr[b],'fold_validacion']=k+1
    partition.to_csv(OUT/'particiones.csv',index=False)
    specs={
      'Logistica':(LogisticRegression(max_iter=1200,random_state=SEED),{'C':[.1,1.]}),
      'RandomForest':(RandomForestClassifier(n_estimators=180,max_depth=12,n_jobs=2,random_state=SEED),{'min_samples_leaf':[5,20]}),
      'XGBoost':(XGBClassifier(n_estimators=160,learning_rate=.05,subsample=.85,colsample_bytree=.85,n_jobs=2,random_state=SEED,eval_metric='logloss'),{'max_depth':[2,4]}),
      'LightGBM':(LGBMClassifier(n_estimators=160,learning_rate=.05,verbosity=-1,n_jobs=2,random_state=SEED),{'num_leaves':[7,15]})}
    runs=[]; summaries=[];fitted={};oof={}
    for name,(est,grid) in specs.items():
        best=-1
        for params in ParameterGrid(grid):
            ps=np.zeros(len(tr));scores=[]
            for k,(a,b) in enumerate(folds,1):
                p=Pipeline([('preparar',prep()),('modelo',clone(est).set_params(**params))])
                ia,ib=tr[a],tr[b]
                p.fit(X.iloc[ia],y[ia],modelo__sample_weight=compute_sample_weight('balanced',y[ia]))
                prob=p.predict_proba(X.iloc[ib])[:,1];ps[b]=prob;m=metricas(y[ib],prob);scores.append(m)
                runs.append({'modelo':name,'parametros':json.dumps(params),'fold':k,**m})
            ap=np.mean([s['PR_AUC_AP'] for s in scores])
            print(name,params,'AP CV',round(ap,4),flush=True)
            if ap>best:best=ap;chosen=params;bestps=ps.copy();bestscores=scores
        summaries.append({'modelo':name,'parametros':json.dumps(chosen),**{f'CV_{c}':np.mean([s[c] for s in bestscores]) for c in bestscores[0]},'CV_AP_sd':np.std([s['PR_AUC_AP'] for s in bestscores],ddof=1)})
        fitted[name]=Pipeline([('preparar',prep()),('modelo',clone(est).set_params(**chosen))]).fit(X.iloc[tr],y[tr],modelo__sample_weight=compute_sample_weight('balanced',y[tr]))
        oof[name]=bestps
    cv=pd.DataFrame(summaries).sort_values('CV_PR_AUC_AP',ascending=False);winner=cv.iloc[0].modelo
    cv.to_csv(OUT/'comparacion_validacion.csv',index=False);pd.DataFrame(runs).to_csv(OUT/'experimentos_folds.csv',index=False)
    tests=[]
    for name,p in fitted.items():tests.append({'modelo':name,**metricas(y[te],p.predict_proba(X.iloc[te])[:,1])})
    pd.DataFrame(tests).to_csv(OUT/'comparacion_test.csv',index=False)
    best=fitted[winner];prob=best.predict_proba(X.iloc[te])[:,1]
    joblib.dump(best,OUT/'modelo_ganador.joblib')
    pd.DataFrame({'fila':tr,'real':y[tr],'probabilidad_oof':oof[winner]}).to_csv(OUT/'predicciones_oof.csv',index=False)
    err=d.iloc[te][['conglome','ubigeo','rural','lengua','rezago','internet_hogar','ratio_alumno_docente']].copy()
    err['fila']=te;err['probabilidad']=prob;err['prediccion']=(prob>=.5).astype(int)
    err['resultado']=np.select([(y[te]==1)&(prob<.5),(y[te]==0)&(prob>=.5)],['falso_negativo','falso_positivo'],default='correcto')
    err.to_csv(OUT/'predicciones_test.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,3.5))
    for i,(name,p) in enumerate(fitted.items()):
        pr=p.predict_proba(X.iloc[te])[:,1];fpr,tpr,_=roc_curve(y[te],pr);prec,rec,_=precision_recall_curve(y[te],pr)
        axes[0].plot(fpr,tpr,label=name,color=COLORS[i]);axes[1].plot(rec,prec,label=name,color=COLORS[i])
    axes[0].plot([0,1],[0,1],'k--',lw=1);axes[1].axhline(y[te].mean(),color='gray',ls='--')
    axes[0].set(xlabel='Falsos positivos',ylabel='Sensibilidad',title='ROC en test agrupado');axes[1].set(xlabel='Sensibilidad',ylabel='Precisión',title='Precision Recall en test');axes[1].legend(fontsize=8);guardar('roc_pr')
    fig,axes=plt.subplots(1,2,figsize=(9,3.6));cm=confusion_matrix(y[te],prob>=.5)
    ConfusionMatrixDisplay(cm,display_labels=['Sin desfase','Con desfase']).plot(ax=axes[0],colorbar=False,cmap='Blues')
    obs,pred=calibration_curve(y[te],prob,n_bins=8,strategy='quantile')
    axes[1].plot(pred,obs,'o-',color=COLORS[0],label=winner);axes[1].plot([0,1],[0,1],'k--');axes[1].set(xlabel='Probabilidad media',ylabel='Frecuencia observada',title='Calibración sin reajuste');guardar('confusion_calibracion')
    # Sensibilidad geográfica con hiperparámetros ya fijados; no reemplaza el test principal.
    ga,gb=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=SEED).split(X,y,d.ubigeo))
    geo=clone(best).fit(X.iloc[ga],y[ga],modelo__sample_weight=compute_sample_weight('balanced',y[ga]))
    # Sensibilidad de definición: dos o más años, reportada como objetivo distinto.
    y2=d.atraso_dos_anios.to_numpy();alt=clone(best).fit(X.iloc[tr],y2[tr],modelo__sample_weight=compute_sample_weight('balanced',y2[tr]))
    valid=d.FACPOB07.iloc[te].notna().to_numpy();weights=d.FACPOB07.iloc[te].to_numpy()
    weighted=metricas(y[te][valid],prob[valid],weights[valid])
    # IC por remuestreo de conglomerados completos del test.
    rng=np.random.default_rng(SEED);groups=np.unique(g[te]);indices={v:np.flatnonzero(g[te]==v) for v in groups};boot=[]
    for _ in range(300):
        ids=np.concatenate([indices[v] for v in rng.choice(groups,len(groups),replace=True)])
        if len(np.unique(y[te][ids]))==2:boot.append(metricas(y[te][ids],prob[ids]))
    intervals={c:np.quantile([m[c] for m in boot],[.025,.975]).tolist() for c in boot[0]}
    summary={'ganador':winner,'criterio':'Mayor AP media en validacion GroupKFold de train; test no elige modelo ni parametros.',
      'n_train':len(tr),'n_test':len(te),'conglomerados_train':len(set(g[tr])),'conglomerados_test':len(set(g[te])),'solapamiento':0,
      'prevalencia_test':y[te].mean(),'test':metricas(y[te],prob),'IC95_bootstrap_conglomerados':intervals,'matriz_confusion':cm.tolist(),
      'sensibilidad_distrito':metricas(y[gb],geo.predict_proba(X.iloc[gb])[:,1]),
      'sensibilidad_atraso_2_anios':metricas(y2[te],alt.predict_proba(X.iloc[te])[:,1]),'sensibilidad_FACPOB07':weighted,
      'nota_pesos':'Balance de clases solo en train por fold. FACTOR07 se conserva; FACPOB07 solo sensibilidad descriptiva, sin inferencia nacional del panel.',
      'predictores':NUM+CAT,'exclusiones':sorted(FORBIDDEN),'umbral':.5}
    dump('resumen_modelos',summary);print(json.dumps(summary,indent=2,ensure_ascii=False),flush=True)
    return tr,te,best

def perfiles(d,tr,te):
    # El clustering de recursos no incorpora el resultado. Se perfila rezago después.
    cols=['rural','electricidad','internet_hogar','uso_internet','frecuencia_tic','log_ingreso_pc','log_gasto_pc','miembros_hogar','ratio_alumno_docente','proporcion_publica']
    pre=Pipeline([('imputar',SimpleImputer(strategy='median',keep_empty_features=True)),('escalar',StandardScaler())])
    A=pre.fit_transform(d.iloc[tr][cols]);B=pre.transform(d.iloc[te][cols]);rng=np.random.default_rng(SEED)
    sample=rng.choice(len(A),min(1800,len(A)),replace=False);rows=[];models={}
    for k in range(2,7):
        for alg in ['KMeans','GMM']:
            m=KMeans(n_clusters=k,n_init=15,random_state=SEED) if alg=='KMeans' else GaussianMixture(n_components=k,n_init=2,reg_covar=1e-4,random_state=SEED)
            m.fit(A);lab=m.predict(A[sample]);models[(alg,k)]=m
            rows.append({'algoritmo':alg,'k':k,'silueta':silhouette_score(A[sample],lab),'Davies_Bouldin':davies_bouldin_score(A[sample],lab),'Calinski_Harabasz':calinski_harabasz_score(A[sample],lab)})
    comp=pd.DataFrame(rows).sort_values('silueta',ascending=False);comp.to_csv(OUT/'comparacion_clustering.csv',index=False)
    win=comp.iloc[0];m=models[(win.algoritmo,int(win.k))];labels=np.empty(len(d),int);labels[tr]=m.predict(A);labels[te]=m.predict(B)
    prof=d[cols+['rezago','atraso_dos_anios','anios_desfase']].copy();prof['cluster']=labels
    table=prof.groupby('cluster').mean();table['n']=prof.groupby('cluster').size()
    table['nombre']=[('Rural' if r.rural>.5 else 'Urbano')+(' con baja conexión' if r.internet_hogar<.5 else ' con conexión mayoritaria')+f' y ratio docente {r.ratio_alumno_docente:.1f}' for _,r in table.iterrows()]
    table.to_csv(OUT/'perfiles_clusters.csv');pd.DataFrame({'fila':range(len(d)),'cluster':labels}).to_csv(OUT/'asignacion_clusters.csv',index=False)
    fig,axes=plt.subplots(1,3,figsize=(12,3))
    for alg in ['KMeans','GMM']:
        s=comp[comp.algoritmo==alg].sort_values('k')
        for ax,col in zip(axes,['silueta','Davies_Bouldin','Calinski_Harabasz']):ax.plot(s.k,s[col],'o-',label=alg);ax.set(xlabel='k',title=col)
    axes[0].legend();guardar('seleccion_clusters')
    pca=PCA(2,random_state=SEED).fit(A);coords=pca.transform(A);show=rng.choice(len(A),min(4000,len(A)),replace=False)
    fig,axes=plt.subplots(1,2,figsize=(10,3.6));axes[0].scatter(coords[show,0],coords[show,1],c=labels[tr][show],cmap='tab10',s=7,alpha=.45)
    axes[0].set(xlabel='PC1',ylabel='PC2',title='Perfiles de recursos en train')
    sil=silhouette_samples(A[sample],m.predict(A[sample]));sl=m.predict(A[sample]);low=0
    for k in np.unique(sl):
        vals=np.sort(sil[sl==k]);axes[1].fill_betweenx(np.arange(low,low+len(vals)),0,vals,alpha=.65);low+=len(vals)+15
    axes[1].axvline(sil.mean(),ls='--',color='black');axes[1].set(xlabel='Silueta',yticks=[],title='Cohesión y separación');guardar('pca_siluetas')
    dump('resumen_clustering',{'ganador':win.to_dict(),'varianza_PCA':pca.explained_variance_ratio_.tolist(),'variables':cols,'regla':'Ajuste y seleccion en train; test se asigna por predict. Rezago y anos de desfase solo caracterizan grupos, no los construyen.'})
    return labels

def doble_desventaja(d,tr,te):
    # Umbral contextual fijado en train, antes de mirar las tasas de test.
    q=float(d.ratio_alumno_docente.iloc[tr].quantile(.75))
    rows=[];rng=np.random.default_rng(SEED)
    for split,ids in [('train',tr),('test',te)]:
        s=d.iloc[ids].dropna(subset=['internet_hogar','ratio_alumno_docente']).copy()
        s['sin_internet']=s.internet_hogar.eq(0);s['ratio_alto']=s.ratio_alumno_docente.ge(q)
        s['grupo']=s.sin_internet.astype(int)*2+s.ratio_alto.astype(int)
        for group in range(4):
            a=s.loc[s.grupo.eq(group)];g=a.groupby('conglome').rezago.agg(['sum','count'])
            boots=[]
            for _ in range(400):
                ids2=rng.integers(0,len(g),len(g));v=g.iloc[ids2];boots.append(v['sum'].sum()/v['count'].sum())
            lo,hi=np.quantile(boots,[.025,.975]);rows.append({'particion':split,'grupo':group,'n':len(a),'conglomerados':len(g),'tasa_rezago':a.rezago.mean(),'tasa_atraso_2':a.atraso_dos_anios.mean(),'sin_desfase':int(a.rezago.eq(0).sum()),'IC95_inf':lo,'IC95_sup':hi})
    t=pd.DataFrame(rows);t.to_csv(OUT/'doble_desventaja.csv',index=False)
    v=t[t.particion.eq('test')].set_index('grupo');contrast=v.loc[3,'tasa_rezago']-v.loc[2,'tasa_rezago']-v.loc[1,'tasa_rezago']+v.loc[0,'tasa_rezago']
    fig,ax=plt.subplots(figsize=(7.4,3.4));x=np.arange(4);ax.bar(x,v.tasa_rezago,color=[COLORS[0],COLORS[1],COLORS[2],COLORS[3]],width=.65)
    ax.errorbar(x,v.tasa_rezago,yerr=[v.tasa_rezago-v.IC95_inf,v.IC95_sup-v.tasa_rezago],fmt='none',color='black',capsize=4)
    ax.set(xticks=x,xticklabels=['Con conexión\nRatio menor','Con conexión\nRatio alto','Sin conexión\nRatio menor','Sin conexión\nRatio alto'],ylabel='Proporción con desfase',title='Acumulación de desventajas en test')
    for i,r in v.iterrows():ax.text(i,r.IC95_sup+.01,f'n={int(r.n)}',ha='center',fontsize=9)
    ax.set_ylim(0,min(1,v.IC95_sup.max()+.1));guardar('doble_desventaja')
    dump('resumen_desventaja',{'umbral_ratio_train_P75':q,'contraste_aditivo_test':contrast,'interpretacion':'Contraste descriptivo de cuatro tasas crudas; no estima efecto causal ni interaccion ajustada. Ratio alto significa P75 de la muestra train, no norma MINEDU.','casos_sin_desfase_doble_desventaja_test':int(v.loc[3,'sin_desfase'])})

def explicar(d,tr,te,best):
    import shap
    rng=np.random.default_rng(SEED);ids=rng.choice(te,min(350,len(te)),replace=False)
    pre=best.named_steps['preparar'];model=best.named_steps['modelo'];names=list(pre.get_feature_names_out())
    A=pre.transform(d.iloc[ids][NUM+CAT]);bg=pre.transform(d.iloc[rng.choice(tr,80,replace=False)][NUM+CAT])
    # Fondo interventional tomado exclusivamente de train.
    if isinstance(model,LogisticRegression):
        ex=shap.LinearExplainer(model,bg);exp=ex(A)
    else:
        ex=shap.TreeExplainer(model,data=bg,feature_perturbation='interventional',model_output='raw');exp=ex(A,check_additivity=False)
    if exp.values.ndim==3:exp=exp[:,:,1]
    values=exp.values;probs=best.predict_proba(d.iloc[ids][NUM+CAT])[:,1];real=d.rezago.iloc[ids].to_numpy()
    # Cambiar los valores mostrados a unidades originales; SHAP conserva la salida del modelo.
    display=A.copy()
    for j,c in enumerate(NUM):display[:,j]=d.iloc[ids][c].fillna(pre.named_transformers_['num'].named_steps['imputar'].statistics_[j]).to_numpy()
    shown=shap.Explanation(values=values,base_values=exp.base_values,data=display,feature_names=names)
    shap.plots.beeswarm(shown,max_display=10,group_remaining_features=False,show=False);guardar('shap_global')
    for name,color,out in [('internet_hogar','lengua_1','shap_dependencia_internet'),('ratio_alumno_docente','rural','shap_dependencia_ratio')]:
        j=names.index(name);cj=names.index(color) if color in names else names.index('rural')
        fig,ax=plt.subplots(figsize=(6.3,3.6));sc=ax.scatter(display[:,j],values[:,j],c=display[:,cj],cmap='viridis',s=16,alpha=.6);fig.colorbar(sc,ax=ax,label=color)
        ax.set(xlabel=name,ylabel='Contribución SHAP',title='Dependencia y contexto');guardar(out)
    cases={}
    for label,mask,order in [('alto',(real==1)&(probs>=.5),np.argmax),('bajo',(real==0)&(probs<.5),np.argmin)]:
        valid=np.flatnonzero(mask)
        assert len(valid),f'No hay casos correctamente clasificados para {label}'
        i=valid[order(probs[valid])];shap.plots.waterfall(shown[int(i)],max_display=10,show=False);guardar('shap_caso_'+label)
        cases[label]={'fila':int(ids[i]),'real':int(real[i]),'probabilidad':float(probs[i])}
    importance=pd.DataFrame({'variable':names,'SHAP_abs_medio':np.abs(values).mean(axis=0)}).sort_values('SHAP_abs_medio',ascending=False);importance.to_csv(OUT/'importancia_shap.csv',index=False)
    raw=exp.base_values+values.sum(axis=1)
    predraw=model.decision_function(A) if isinstance(model,LogisticRegression) else (model.predict(A,raw_score=True) if isinstance(model,LGBMClassifier) else (model.predict(A,output_margin=True) if isinstance(model,XGBClassifier) else model.predict_proba(A)[:,1]))
    dump('resumen_shap',{'casos':cases,'muestra':len(ids),'fondo_train':len(bg),'error_aditividad_max':float(np.max(np.abs(raw-predraw))),'nota':'Scatter coloreado describe dependencia; no calcula valores formales de interaccion ni causalidad.'})
    np.savez_compressed(OUT/'valores_shap.npz',values=values,base=exp.base_values,filas=ids)

if __name__=='__main__':
    d=cargar();tr,te,best=entrenar(d);perfiles(d,tr,te);doble_desventaja(d,tr,te);explicar(d,tr,te,best)
