"""Build the single Chapter 4 main-text candidate figure/table set.

This is a presentation-only layer: it reads locked labels and current formal
output tables, never fits/relabels a model or recomputes a statistical test.
"""
import os
from pathlib import Path
import json
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Patch
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = Path(os.environ.get("CASA_FYP_SOURCE_ROOT", ROOT / "authorised_data")).expanduser().resolve()
OUT = ROOT / "results" / "generated_figures"
OUT.mkdir(parents=True, exist_ok=True)
RAIL = ROOT / "analysis" / "02_mode_specific_clustering" / "rail" / "outputs" / "data"
BUSROOT = ROOT / "analysis" / "02_mode_specific_clustering" / "bus" / "outputs_1805_min33"
RQ2 = ROOT / "analysis" / "03_lnwc_context" / "outputs"
CTX = ROOT / "analysis" / "04_urban_context" / "outputs"
BOUNDARY = SOURCE_ROOT / "map" / "London_LSOA_2021_Boundaries.geojson"
RAIL_COORDS = ROOT / "analysis" / "01_data_preparation" / "rail" / "outputs" / "data" / "rail_allmodes_coords.csv"

RC = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9"]
BC = ["#4C93D3", "#D1284B", "#00A6A6", "#1B3A6B"]
MOVE = {"entry": ("Entry", "#222222", "-"), "exit": ("Exit", "#757575", "--"),
        "boardings": ("Boarding", "#222222", "-"), "alightings": ("Alighting", "#757575", "--")}

def labels(mode):
    if mode == "rail":
        names = pd.read_csv(RAIL / "rail_cluster_names.csv")
        labs = pd.read_csv(RAIL / "rail_allmodes_k5_labels.csv").rename(columns={"unit":"id"})
    else:
        names = pd.read_csv(BUSROOT / "data" / "bus_cluster_names.csv")
        labs = pd.read_csv(BUSROOT / "clr" / "labels" / "k4_labels.csv").query("retained_for_fit").rename(columns={"lsoa":"id"})
    return labs, names.set_index("cluster")

def write_tables():
    rl, rn = labels("rail"); bl, bn = labels("bus")
    rows=[]
    for mode, labs, names, unit, cov in [("Rail",rl,rn,"Station","Diagonal"),("Bus",bl,bn,"LSOA","Full")]:
        n=len(labs)
        for c, count in labs.cluster.value_counts().sort_index().items():
            rows.append([mode,unit,n,len(names),cov,f"C{c}",int(count),count/n, names.loc[c,"name_en"]])
    pd.DataFrame(rows,columns=["Mode","Analytical unit","Total n","Final K","Covariance","Cluster","Cluster n","Share","Short descriptor"]).to_csv(OUT/"Table_4_1_cluster_solution.csv",index=False)
    sig=pd.concat([pd.read_csv(RQ2/"data"/"rail_cluster_metric_significance.csv"),pd.read_csv(RQ2/"data"/"bus_cluster_metric_significance.csv")])
    sig["Mode"]=sig["mode"].str.title(); sig["Descriptor"]=sig.metric.str.replace("_"," ")
    sig[["Mode","Descriptor","n","kruskal_H","p_bh","epsilon_squared"]].rename(columns={"n":"Valid n","kruskal_H":"Kruskal-Wallis H","p_bh":"BH-adjusted p","epsilon_squared":"epsilon-squared"}).to_csv(OUT/"Table_4_2_behavioural_descriptor_tests.csv",index=False)
    ln=pd.read_csv(RQ2/"data"/"lnwc_statistical_summary.csv")
    keep=ln[ln["analysis"].str.contains("chi_square")].copy(); keep["Mode"]=keep["mode"].str.title()
    keep["Brief bounded interpretation"]="Exploratory area-level association; no spatial-autocorrelation adjustment."
    keep[["Mode","n","chi_square","cramers_v","p_value","Brief bounded interpretation"]].rename(columns={"n":"Eligible sample","chi_square":"chi-square","cramers_v":"Cramer's V","p_value":"p"}).to_csv(OUT/"Table_4_3_lnwc_association.csv",index=False)
    return rl,rn,bl,bn

def temporal(mode,labs,names):
    if mode=="rail":
        long=pd.read_parquet(ROOT/"analysis"/"01_data_preparation"/"rail"/"outputs"/"preprocessed"/"numbat_allmodes_station_qhr_all_daytypes_final.parquet")
        long["id"]=long.NLC.astype(str); labs=labs.assign(id=labs.id.astype(str)); long=long[long.extended_minute.between(1080,1739)].copy(); long["hour"]=(long.extended_minute//60)*60
        days=["MON","TWT","FRI","SAT","SUN"]; dirs=["entry","exit"]; palette=RC; title="Rail station profiles: 18:00–05:00, n=403"
    else:
        long=pd.read_parquet(ROOT/"analysis"/"01_data_preparation"/"bus"/"outputs_1805_min33"/"preprocessed"/"bus_lsoa_night_long.parquet")
        long["id"]=long.lsoa.astype(str); long=long[long.hour_bin.between(1080,1680)].copy(); long["hour"]=long.hour_bin
        days=["Weekday","Saturday","Sunday"]; dirs=["boardings","alightings"]; palette=BC; title="Bus LSOA profiles: 18:00–05:00, n=3,383"
    long["total"]=long.groupby(["id","direction"])["count"].transform("sum")
    long["share"]=long["count"]/long["total"].replace(0,np.nan)
    dat=long.merge(labs[["id","cluster"]],on="id",how="inner").groupby(["cluster","day_type","direction","hour"],as_index=False).share.mean()
    fig,axes=plt.subplots(len(names),len(days),figsize=(13,10 if mode=="rail" else 8),sharey=True)
    ymax=dat.share.max()*1.08
    for c in range(len(names)):
      for j,d in enumerate(days):
        ax=axes[c,j]; sub=dat[(dat.cluster==c)&(dat.day_type==d)]
        for direction in dirs:
          q=sub[sub.direction==direction].sort_values("hour"); lab,col,style=MOVE[direction]
          ax.plot(q.hour,q.share*100,color=col,linestyle=style,lw=1.5,label=lab if c==0 and j==0 else None)
        ax.axvline(1440,color="#999",ls=":",lw=.8); ax.set_ylim(0,ymax*100); ax.grid(alpha=.2)
        ax.set_xticks(range(1080,1741,120)); ax.set_xticklabels([f"{(x//60)%24:02d}" for x in range(1080,1741,120)],fontsize=7)
        if j==0: ax.set_ylabel(f"C{c} {names.loc[c,'short']}\n% of unit week",fontsize=8,color=palette[c])
        if c==0: ax.set_title(d,fontsize=9)
    axes[0,0].legend(frameon=False,fontsize=8); fig.suptitle(title,y=.995)
    fig.tight_layout(); fig.savefig(OUT/f"Figure_4_{'2' if mode=='rail' else '4'}_{mode}_temporal_profiles.png",dpi=260); plt.close(fig)

ENTRY_COL = "#0072B2"
EXIT_COL = "#D55E00"
CLUSTER_DAY_STYLE = {
    "SAT": dict(ls="-.", lw=2.1, alpha=0.95, zorder=5),
    "TWT": dict(ls="-",  lw=1.9, alpha=0.85, zorder=4),
    "FRI": dict(ls=":",  lw=1.3, alpha=0.55, zorder=2),
    "SUN": dict(ls=(0, (3, 1, 1, 1)), lw=1.1, alpha=0.50, zorder=1),
}
CLUSTER_DAY_ORDER = ["FRI", "SUN", "TWT", "SAT"]
CLUSTER_DAY_LABEL = {"TWT": "Weekdays", "FRI": "Friday", "SAT": "Saturday", "SUN": "Sunday"}

def temporal_by_cluster_rail(labs, names):
    """Companion view to temporal('rail', ...): one panel per cluster instead
    of per day-type, Saturday drawn on top (the real story is a weekday vs
    Saturday entry/exit dominance reversal, confirmed for all 5 clusters --
    large for C0/C1/C4, negligible for C2), with hand-placed annotations
    checked against the underlying hourly series rather than templated.
    Kept as a separate main-text candidate alongside temporal('rail', ...),
    which is retained unchanged as the appendix reference figure.
    """
    from matplotlib.lines import Line2D
    long = pd.read_parquet(ROOT / "analysis" / "01_data_preparation" / "rail" / "outputs" / "preprocessed" / "numbat_allmodes_station_qhr_all_daytypes_final.parquet")
    long["id"] = long.NLC.astype(str)
    labs = labs.assign(id=labs.id.astype(str))
    long = long[long.extended_minute.between(1080, 1739)].copy()
    long["hour"] = (long.extended_minute // 60) * 60
    long["total"] = long.groupby(["id", "direction"])["count"].transform("sum")
    long["share"] = long["count"] / long["total"].replace(0, np.nan)
    dat = (long.merge(labs[["id", "cluster"]], on="id", how="inner")
           .groupby(["cluster", "day_type", "direction", "hour"], as_index=False, observed=True).share.mean())

    def val(cluster, day, direction, hour):
        q = dat[(dat.cluster == cluster) & (dat.day_type == day) & (dat.direction == direction) & (dat.hour == hour)]
        return float(q.share.iloc[0]) * 100

    def hour_label(h):
        return f"{(h // 60) % 24:02d}:00"

    def annotate(ax, xy, text, col, dx, dy, ha="left"):
        ax.annotate(text, xy=xy, xytext=(xy[0] + dx, xy[1] + dy), fontsize=8.0, color=col, ha=ha,
                    fontweight="medium", arrowprops=dict(arrowstyle="-|>", color=col, lw=1.0, alpha=0.9))

    n_clusters = len(names)
    ncols, nrows = 2, 3
    fig, axes = plt.subplots(nrows, ncols, figsize=(13, 12.5), sharey=True)
    axes_flat = axes.flatten()
    hticks = list(range(1080, 1741, 120))
    global_ymax = dat.share.max() * 100 * 1.16

    for c in range(n_clusters):
        ax = axes_flat[c]
        sub_c = dat[dat.cluster == c]
        for direction, col in [("entry", ENTRY_COL), ("exit", EXIT_COL)]:
            for day in CLUSTER_DAY_ORDER:
                q = sub_c[(sub_c.direction == direction) & (sub_c.day_type == day)].sort_values("hour")
                if q.empty:
                    continue
                ax.plot(q.hour, q.share * 100, color=col, **CLUSTER_DAY_STYLE[day])
        ax.set_xlim(1080, 1739); ax.set_xticks(hticks)
        ax.set_xticklabels([hour_label(h) for h in hticks], fontsize=8)
        ax.grid(alpha=0.2); ax.axvline(1440, color="#999999", ls=":", lw=0.8)
        ax.set_ylim(0, global_ymax)
        if c % ncols == 0: ax.set_ylabel("% of unit week", fontsize=9)
        ax.set_title(f"C{c} {names.loc[c, 'short']}", fontsize=11, fontweight="bold", loc="left")

    # -- annotations verified against the hourly series (see conversation log);
    # deliberately varied in structure per panel, not a filled-in template --
    annotate(axes_flat[0], (1140, val(0, "SAT", "entry", 1140)),
             "Sharpest weekday→Saturday\nreversal of the five clusters", ENTRY_COL, dx=100, dy=0.55)
    annotate(axes_flat[0], (1500, val(0, "TWT", "exit", 1500)),
             "Falls to near zero\nby 01:00", EXIT_COL, dx=90, dy=0.55)

    annotate(axes_flat[1], (1320, val(1, "TWT", "entry", 1320)),
             "Entry rebounds at 22:00 —\nunique to this cluster", ENTRY_COL, dx=110, dy=0.55)

    annotate(axes_flat[2], (1260, val(2, "TWT", "entry", 1260)),
             "Closely matched on both\nweekday and weekend", ENTRY_COL, dx=140, dy=0.65)
    annotate(axes_flat[2], (1140, val(2, "TWT", "entry", 1140)),
             "Most activity concentrated\nby 20:00", EXIT_COL, dx=90, dy=0.85)

    annotate(axes_flat[3], (1380, val(3, "SAT", "entry", 1380)),
             "Saturday entries stay\nelevated into late evening", ENTRY_COL, dx=80, dy=0.45)
    annotate(axes_flat[3], (1620, val(3, "SAT", "entry", 1620)),
             "Only cluster with activity\npersisting past 01:00", EXIT_COL, dx=-10, dy=0.75, ha="center")

    annotate(axes_flat[4], (1140, val(4, "SAT", "entry", 1140)),
             "Same Saturday reversal as C0,\nbut milder (0.30 vs 0.55 pp)", ENTRY_COL, dx=100, dy=0.55)

    for c in range(n_clusters, nrows * ncols):
        axes_flat[c].axis("off")

    legend_ax = axes_flat[-1]
    handles = [Line2D([0], [0], color=ENTRY_COL, lw=2.2, label="Entry"),
               Line2D([0], [0], color=EXIT_COL, lw=2.2, label="Exit")]
    handles += [Line2D([0], [0], color="#444444", label=CLUSTER_DAY_LABEL[day],
                        **{k: v for k, v in CLUSTER_DAY_STYLE[day].items() if k != "zorder"})
                for day in ["TWT", "FRI", "SAT", "SUN"]]
    legend_ax.legend(handles=handles, loc="center", frameon=False, fontsize=10, ncol=2,
                      title="Movement (colour)  /  Day type (line style)")

    fig.suptitle("Rail station profiles by cluster: 18:00–05:00, n=403", fontsize=13, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97]); fig.subplots_adjust(hspace=0.45, wspace=0.25)
    fig.savefig(OUT / "Figure_4_2b_rail_temporal_profiles_by_cluster.png", dpi=260, bbox_inches="tight")
    plt.close(fig)

BUS_DAY_STYLE = {
    "Weekday":  dict(ls="-",  lw=2.0, alpha=0.90, zorder=3),
    "Saturday": dict(ls="-.", lw=1.4, alpha=0.70, zorder=2),
    "Sunday":   dict(ls=(0, (3, 1, 1, 1)), lw=1.3, alpha=0.65, zorder=1),
}
BUS_DAY_ORDER = ["Sunday", "Saturday", "Weekday"]  # draw order back-to-front

def temporal_by_cluster_bus(labs, names):
    """Bus companion to temporal_by_cluster_rail: one panel per cluster,
    boardings/alightings as colour, Weekday/Saturday/Sunday as line style
    (bus day-type is natively this 3-way split -- no Friday/Monday distinction
    exists in the bus pipeline). No annotations yet -- base layer only, to be
    annotated once cluster-specific features are checked against the data,
    same as was done for rail.
    """
    from matplotlib.lines import Line2D
    long = pd.read_parquet(ROOT / "analysis" / "01_data_preparation" / "bus" / "outputs_1805_min33" / "preprocessed" / "bus_lsoa_night_long.parquet")
    long["id"] = long.lsoa.astype(str)
    long = long[long.hour_bin.between(1080, 1680)].copy()
    long["hour"] = long.hour_bin
    long["total"] = long.groupby(["id", "direction"])["count"].transform("sum")
    long["share"] = long["count"] / long["total"].replace(0, np.nan)
    dat = (long.merge(labs[["id", "cluster"]], on="id", how="inner")
           .groupby(["cluster", "day_type", "direction", "hour"], as_index=False, observed=True).share.mean())

    def hour_label(h):
        return f"{(h // 60) % 24:02d}:00"

    n_clusters = len(names)
    fig, axes = plt.subplots(2, 2, figsize=(11, 9.5), sharey=True)
    axes_flat = axes.flatten()
    hticks = list(range(1080, 1681, 120))
    global_ymax = dat.share.max() * 100 * 1.16

    for c in range(n_clusters):
        ax = axes_flat[c]
        sub_c = dat[dat.cluster == c]
        for direction, col in [("boardings", ENTRY_COL), ("alightings", EXIT_COL)]:
            for day in BUS_DAY_ORDER:
                q = sub_c[(sub_c.direction == direction) & (sub_c.day_type == day)].sort_values("hour")
                if q.empty:
                    continue
                ax.plot(q.hour, q.share * 100, color=col, **BUS_DAY_STYLE[day])
        ax.set_xlim(1080, 1680); ax.set_xticks(hticks)
        ax.set_xticklabels([hour_label(h) for h in hticks], fontsize=8)
        ax.grid(alpha=0.2); ax.axvline(1440, color="#999999", ls=":", lw=0.8)
        ax.set_ylim(0, global_ymax)
        if c % 2 == 0: ax.set_ylabel("% of unit week", fontsize=9)
        ax.set_title(f"C{c} {names.loc[c, 'short']}", fontsize=11, fontweight="bold", loc="left")

    handles = [Line2D([0], [0], color=ENTRY_COL, lw=2.2, label="Boardings"),
               Line2D([0], [0], color=EXIT_COL, lw=2.2, label="Alightings")]
    handles += [Line2D([0], [0], color="#444444", label=day,
                        **{k: v for k, v in BUS_DAY_STYLE[day].items() if k != "zorder"})
                for day in ["Weekday", "Saturday", "Sunday"]]
    fig.legend(handles=handles, loc="lower center", frameon=False, fontsize=9.5, ncol=5,
               bbox_to_anchor=(0.5, -0.02), title="Movement (colour)  /  Day type (line style)")

    fig.suptitle("Bus LSOA profiles by cluster: 18:00–05:00, n=3,383", fontsize=13, y=0.995)
    fig.tight_layout(rect=[0, 0.05, 1, 0.97])
    fig.savefig(OUT / "Figure_4_4b_bus_temporal_profiles_by_cluster.png", dpi=260, bbox_inches="tight")
    plt.close(fig)

def heatmap(mode):
    file="rail_enrichment.csv" if mode=="rail" else "bus_enrichment.csv"; d=pd.read_csv(RQ2/"data"/file,index_col="cluster")
    fig,ax=plt.subplots(figsize=(8,3.5)); im=ax.imshow(d,aspect="auto",cmap="RdBu_r",norm=TwoSlopeNorm(vmin=0,vcenter=1,vmax=max(2,d.to_numpy().max())))
    ax.set_xticks(range(7),[f"LNWC {i}" for i in range(1,8)]); ax.set_yticks(range(len(d)),[f"C{i}" for i in d.index]);
    for i in range(len(d)):
      for j in range(7): ax.text(j,i,f"{d.iloc[i,j]:.2f}",ha="center",va="center",fontsize=8)
    fig.colorbar(im,ax=ax,label="Enrichment ratio (ER=1 neutral)"); ax.set_title(f"{mode.title()} LNWC enrichment; mode-specific eligible benchmark")
    fig.tight_layout(); fig.savefig(OUT/f"Figure_4_{'6' if mode=='rail' else '7'}_{mode}_lnwc_enrichment.png",dpi=260); plt.close(fig)

def _display(s):
    return s.replace("_", " ")

CONTEXT_VAR_LABELS = {
    "no_car_household_share": "Households without car access",
    "age_20_34_share": "Residents aged 20–34",
    "dependent_children_share": "Households with dependent children",
    "private_rented_share": "Private rented households",
    "log1p_poi_count": "POI intensity (log1p)",
    "population_density": "Population density",
    "transport_storage_share": "Transport & storage employment",
    "social_rented_share": "Social rented households",
    "accom_food_share": "Accommodation & food employment",
    "manufacturing_share": "Manufacturing employment",
    "unemployed_share": "Unemployed residents",
    "shannon_group": "POI diversity (Shannon H)",
    "imd_health": "IMD health deprivation",
}

def context(mode):
    """Main-text context figure: ranking only, deliberately not a mini table."""
    a=pd.read_csv(CTX/"data"/"association_tests.csv")
    a=a[a["mode"]==mode].sort_values(["epsilon_squared","variable"],ascending=[True,True]).tail(10)
    # Squared off (was 10.3:4.0, a fixed Word-frame ratio) to sit closer to this
    # LaTeX build's other Chapter 4 figure proportions.
    fig,ax=plt.subplots(figsize=(7.2,6.0))
    y=np.arange(len(a))
    ax.hlines(y,0,a.epsilon_squared,color="#A6A6A6",lw=1.2,zorder=1)
    ax.scatter(a.epsilon_squared,y,s=58,color="#333333",zorder=2)
    ax.set_yticks(y,[CONTEXT_VAR_LABELS.get(v,_display(v)) for v in a.variable],fontsize=9)
    ax.set_xlabel("Kruskal–Wallis effect size (ε²)")
    ax.set_title(f"{mode.title()} contextual variables: effect-size ranking",loc="left",weight="bold")
    ax.grid(axis="x",alpha=.22); ax.spines[["top","right","left"]].set_visible(False)
    ax.set_axisbelow(True); fig.tight_layout()
    fig.savefig(OUT/f"Figure_4_{'8' if mode=='rail' else '9'}_{mode}_context.png",dpi=300,bbox_inches="tight")
    plt.close(fig)

# Presentation-styled twin of analysis/04_urban_context/src/04_build_figures.py's
# draw_heatmap(). That script stays the unstyled "formal" analysis output (do not
# edit its labels); this is the dissertation-facing relabelled/reformatted copy,
# same source CSVs, same numbers, different presentation only.
CONTEXT_HEATMAP_BLOCKS = [
    ("Disadvantage", ["imd_education", "imd_health", "deprived_1plus_share"]),
    ("Housing", ["private_rented_share", "social_rented_share"]),
    ("Vehicle access & age", ["no_car_household_share", "age_20_34_share"]),
    ("Night labour, residence side (LNWC-aligned)",
     ["accom_food_share", "transport_storage_share", "admin_support_share",
      "wholesale_retail_share", "health_social_share", "manufacturing_share"]),
    ("Ethnicity", ["asian_share", "black_share"]),
    ("Household & work", ["dependent_children_share", "unemployed_share"]),
    ("Facilities", ["log1p_poi_count", "shannon_group"]),
    ("Control", ["population_density"]),
]
CONTEXT_HEATMAP_LABELS = {
    "imd_education": "IMD education",
    "imd_health": "IMD health",
    "deprived_1plus_share": "Deprived households (≥1 dimension)",
    "private_rented_share": "Private rented households",
    "social_rented_share": "Social rented households",
    "no_car_household_share": "Households without car/van",
    "age_20_34_share": "Residents aged 20–34",
    "accom_food_share": "Accommodation & food",
    "transport_storage_share": "Transport & storage",
    "admin_support_share": "Administrative & support services",
    "wholesale_retail_share": "Wholesale & retail",
    "health_social_share": "Health & social work",
    "manufacturing_share": "Manufacturing",
    "asian_share": "Asian",
    "black_share": "Black",
    "dependent_children_share": "Households with dependent children",
    "unemployed_share": "Unemployed",
    "log1p_poi_count": "POI intensity (log1p)",
    "shannon_group": "POI diversity (Shannon H)",
    "population_density": "Population density",
}
CONTEXT_HEATMAP_CLUSTER_LABELS = {
    "rail": {
        "C0 outer arrival-oriented": "C0 Outer arrival",
        "C1 central departure-oriented": "C1 Central departure",
        "C2 central interchange, direction-balanced": "C2 Central balanced",
        "C3 late-night, extended-duration persistent": "C3 Late-night persistent",
        "C4 inner-middle ring mixed": "C4 Inner–middle mixed",
    },
    "bus": {
        "C0 low activity, weak night-persistence": "C0 Low activity",
        "C1 relatively high activity, stronger night-persistence": "C1 High activity / persistent",
        "C2 moderate activity and persistence, transitional": "C2 Moderate / transitional",
        "C3 moderate activity with destination characteristics": "C3 Moderate / alighting-oriented",
    },
}
CONTEXT_HEATMAP_TITLE_LINE1 = {
    "rail": "Standardised contextual profiles of the five Rail usage types",
    "bus": "Standardised contextual profiles of the four Bus usage types",
}

def context_heatmap(mode):
    z=pd.read_csv(CTX/"data"/f"{mode}_cluster_matrix_z.csv",index_col=0)
    stars=pd.read_csv(CTX/"data"/f"{mode}_cluster_matrix_stars.csv",index_col=0).fillna("")
    variables,marks=[],[]
    for label,members in CONTEXT_HEATMAP_BLOCKS:
        present=[v for v in members if v in z.index]
        if not present: continue
        marks.append((label,len(variables))); variables.extend(present)
    z=z.reindex(variables); stars=stars.reindex(variables).reindex(columns=z.columns).fillna("")

    # Sized and set in points for a full-page LaTeX placement, not for inline
    # Word width: the row/column coefficients grew only modestly (~12%) while
    # every font size grew ~25-40%, so text claims a bigger share of the frame
    # and stays legible once the whole image is scaled up to fill a page.
    height=0.36*len(variables)+2.6
    fig,ax=plt.subplots(figsize=(2.3*len(z.columns)+4.8,height))
    limit=float(np.nanmax(np.abs(z.to_numpy()))) or 1.0
    norm=TwoSlopeNorm(vmin=-limit,vcenter=0.0,vmax=limit)
    image=ax.imshow(z.to_numpy(),cmap="RdBu_r",norm=norm,aspect="auto")
    for i in range(z.shape[0]):
        for j in range(z.shape[1]):
            value=z.iat[i,j]
            if not np.isfinite(value): continue
            marker=str(stars.iat[i,j])
            text=f"{value:+.2f}"+(f"\n{marker}" if marker else "")
            ax.text(j,i,text,ha="center",va="center",fontsize=9.5,
                    color="white" if abs(value)>limit*0.6 else "black")

    ax.set_xticks(range(len(z.columns)))
    short_labels=CONTEXT_HEATMAP_CLUSTER_LABELS[mode]
    # Wrapped, not single-line: at the bigger 11pt used for a full-page figure,
    # the longer short-labels (e.g. "C1 High activity / persistent") are wider
    # than one bus column and collide with their neighbour otherwise.
    ax.set_xticklabels([textwrap.fill(short_labels[c],width=15) for c in z.columns],fontsize=11)
    ax.set_yticks(range(len(variables)))
    variable_fontsize=10.5
    ax.set_yticklabels([CONTEXT_HEATMAP_LABELS.get(v,v) for v in variables],fontsize=variable_fontsize)

    for _,row in marks[1:]:
        ax.axhline(row-0.5,color="0.55",linewidth=1.1)
    for label,row in marks:
        wrapped=textwrap.fill(label,width=24)
        ax.text(-0.42,row-0.42,wrapped,fontsize=round(variable_fontsize*0.85,1),
                style="italic",color="#444444",ha="left",va="bottom",
                transform=ax.get_yaxis_transform(which="grid"))

    cbar=fig.colorbar(image,ax=ax,shrink=0.55)
    cbar.set_label("Cluster mean (z-score)",fontsize=12)
    cbar.ax.tick_params(labelsize=10)
    ax.set_title(
        f"{CONTEXT_HEATMAP_TITLE_LINE1[mode]}\n"
        "z-score of cluster mean; stars = cluster-vs-rest Mann-Whitney, BH-corrected "
        "(*** p<0.001, ** p<0.01, * p<0.05)",
        fontsize=13,pad=16,
    )
    fig.tight_layout()
    fig.savefig(OUT/f"Appendix_candidate_{mode}_context_heatmap.png",dpi=300,bbox_inches="tight")
    plt.close(fig)

def context_full_matrix(mode):
    """Appendix candidate only; it is never inserted into the main-text DOCX."""
    z=pd.read_csv(CTX/"data"/f"{mode}_cluster_matrix_z.csv",index_col=0)
    z.index=[_display(str(x)) for x in z.index]
    fig,ax=plt.subplots(figsize=(8.8,7.2 if mode=="rail" else 7.0))
    lim=max(1.0,float(np.abs(z.to_numpy(dtype=float)).max()))
    im=ax.imshow(z,aspect="auto",cmap="RdBu_r",norm=TwoSlopeNorm(vmin=-lim,vcenter=0,vmax=lim))
    ax.set_xticks(range(len(z.columns)),[f"C{i}" for i in range(len(z.columns))])
    ax.set_yticks(range(len(z.index)),z.index,fontsize=8)
    for i in range(len(z.index)):
        for j in range(len(z.columns)):
            val=float(z.iloc[i,j]); ax.text(j,i,f"{val:.2f}",ha="center",va="center",fontsize=6.5,
                                            color="white" if abs(val)>.65*lim else "#222")
    ax.set_title(f"{mode.title()} cluster mean z-scores: complete contextual-variable matrix",loc="left",weight="bold")
    cb=fig.colorbar(im,ax=ax,pad=.02); cb.set_label("within-mode z-score")
    fig.tight_layout()
    fig.savefig(OUT/f"Appendix_Figure_A{'1' if mode=='rail' else '2'}_{mode}_context_full_zscore_matrix.png",dpi=300,bbox_inches="tight")
    plt.close(fig)

BEHAVIOURAL_RANKING_TITLES = {"rail": "(a) Rail behavioural descriptors", "bus": "(b) Bus behavioural descriptors"}
# Both modes' weekend metric read as the same concept (weekend_common_ratio
# for rail, weekend_ratio for bus) so they carry the one display name here.
BEHAVIOURAL_RANKING_LABELS = {
    "weekend_common_ratio": "Weekend-to-weekday ratio",
    "weekend_ratio": "Weekend-to-weekday ratio",
}

def behavioural_effect_ranking_combined():
    """Rail (top) + Bus (bottom) continuous night-use effect-size ranking, one
    figure so the two modes read as a single behavioural-descriptor summary.
    Replaces the former two separate per-mode PNGs."""
    frames={}
    for mode in ("rail","bus"):
        d=pd.read_csv(RQ2/"data"/f"{mode}_cluster_metric_significance.csv")
        frames[mode]=d.sort_values(["epsilon_squared","metric"],ascending=[True,True])
    heights=[len(frames["rail"]),len(frames["bus"])]
    fig,axes=plt.subplots(2,1,figsize=(8.4,0.5*sum(heights)+2.6),
                           gridspec_kw={"height_ratios":heights},sharex=True)
    for ax,mode in zip(axes,("rail","bus")):
        d=frames[mode]
        y=np.arange(len(d))
        ax.hlines(y,0,d.epsilon_squared,color="#A6A6A6",lw=1.2,zorder=1)
        ax.scatter(d.epsilon_squared,y,s=58,color="#333333",zorder=2)
        ax.set_yticks(y,[BEHAVIOURAL_RANKING_LABELS.get(v,_display(v)) for v in d.metric],fontsize=9)
        ax.set_title(BEHAVIOURAL_RANKING_TITLES[mode],loc="left",weight="bold")
        ax.grid(axis="x",alpha=.22); ax.spines[["top","right","left"]].set_visible(False)
        ax.set_axisbelow(True)
    axes[-1].set_xlabel("Kruskal–Wallis effect size (ε²)")
    fig.tight_layout()
    fig.savefig(OUT/"Appendix_candidate_rail_bus_continuous_metric_effect_ranking.png",dpi=300,bbox_inches="tight")
    plt.close(fig)

NIGHT_BEHAVIOUR_LABELS = {
    "log_total_activity": "Night-time activity (log)",
    "direction_balance": "Directional balance",
    "post_2300_share": "Post-23:00 share",
    "weekend_common_ratio": "Weekend-to-weekday ratio",
    "post_midnight_persistence": "Post-midnight persistence",
    "weekend_ratio": "Weekend-to-weekday ratio",
}
_CLUSTER_COUNT_WORDS = {4: "four", 5: "five"}
NIGHT_BEHAVIOUR_TITLES = {
    "rail": "Post-clustering behavioural descriptors for the {count} Rail clusters.",
    "bus": "Post-clustering behavioural descriptors of the {count} Bus usage types.",
}

def night_behaviour_z(mode):
    """Current formal cluster signature: z-score against the mode-wide mean."""
    d=pd.read_csv(RQ2/"data"/f"{mode}_cluster_signature_z.csv").set_index("cluster")
    palette=RC if mode=="rail" else BC
    lim=max(1.0,float(np.abs(d.to_numpy(dtype=float)).max())*1.08)
    height_scale=0.9 if mode=="rail" else 1.0
    fig,axes=plt.subplots(len(d),1,figsize=(8.8,(1.45*len(d)+.7)*height_scale),sharex=True)
    if len(d)==1: axes=[axes]
    for c,ax in zip(d.index,axes):
        values=d.loc[c]
        pos=np.arange(len(values))[::-1]
        ax.barh(pos,values.to_numpy(),color=["#C64036" if v>0 else "#2878B5" for v in values],height=.62)
        ax.axvline(0,color="#333",lw=1.6); ax.grid(axis="x",alpha=.22); ax.set_axisbelow(True)
        ax.set_yticks(pos,[NIGHT_BEHAVIOUR_LABELS.get(x,_display(x)) for x in values.index],fontsize=8)
        ax.set_xlim(-lim,lim); ax.spines[["top","right","left"]].set_visible(False)
        ax.set_title(f"C{c}",loc="left",color=palette[int(c)],weight="bold",fontsize=10)
    axes[-1].set_xlabel(f"Z-score relative to {mode.title()}-wide mean")
    cluster_count=_CLUSTER_COUNT_WORDS.get(len(d),str(len(d)))
    title=NIGHT_BEHAVIOUR_TITLES[mode].format(count=cluster_count)
    fig.suptitle(title,weight="bold",y=.995)
    fig.tight_layout(rect=(0,0,1,.97))
    fig.savefig(OUT/f"Appendix_candidate_{mode}_night_behaviour_z_vs_mode_mean.png",dpi=300,bbox_inches="tight")
    plt.close(fig)

def kselection():
    rb=pd.read_csv(RAIL/"rail_allmodes_k_selection_panel.csv"); bk=pd.read_csv(BUSROOT/"clr"/"diagnostics"/"kdiag.csv")
    # Six diagnostics, same reading order for both modes. Every number plotted
    # here is read straight from each mode's own K-selection CSV -- text
    # anywhere that cites "random-seed ARI"/"bootstrap ARI"/"weakest-cluster
    # Jaccard" for the adopted K must quote these columns' value at that K, not
    # a same-named statistic from a different stability script (e.g.
    # analysis/02_mode_specific_clustering/rail/07_stability_allmodes.py's seed_ARI_mean/
    # bootstrap_ARI_mean_200/weakest_cluster_jaccard use a different reference
    # partition -- agreement WITH the adopted labels -- and a different
    # seed/bootstrap budget, so they are not interchangeable with the columns
    # below even though the English names look alike).
    panels=[
        ("BIC","BIC (lower = better)"),
        ("silhouette","Silhouette (higher = better)"),
        ("davies_bouldin","Davies-Bouldin (lower = better)"),
        ("seed_ari_mean","Random-seed agreement\nmean pairwise ARI"),
        ("bootstrap_ari_mean","Bootstrap stability\nmean ARI"),
        ("bootstrap_min_jaccard_mean","Weakest-cluster reproducibility\nmean matched Jaccard")]
    def plot_panel(axis,d,k,metric,label,mode):
        alternatives={"BIC":"best_BIC", "bootstrap_min_jaccard_mean":"bootstrap_min_cluster_jaccard_mean"}
        col=metric if metric in d else alternatives.get(metric)
        if col is None or col not in d or d[col].dropna().empty:
            axis.set_axis_off(); return
        q=d.dropna(subset=[col]).sort_values("K")
        color="#4C167D" if metric in {"BIC","silhouette","seed_ari_mean","bootstrap_ari_mean"} else "#276749"
        if metric in {"davies_bouldin","bootstrap_min_jaccard_mean"}: color="#A53F3F"
        if metric in {"min_cluster_n"}: color="#777777"
        axis.plot(q.K,q[col],marker="o",ms=4,color=color,lw=1.4)
        axis.axvline(k,color="#D23B31",ls="--",lw=1)
        if k in set(q.K):
            yy=float(q.loc[q.K==k,col].iloc[0]); axis.scatter([k],[yy],s=52,facecolors="none",edgecolors="#D23B31",linewidths=1.5,zorder=4)
        axis.set_title(label,fontsize=8.5); axis.set_xlabel("K",fontsize=8); axis.tick_params(labelsize=7)
        axis.grid(alpha=.18); axis.spines[["top","right"]].set_visible(False)
    def six_panel(d,k,title,path):
        fig,ax=plt.subplots(2,3,figsize=(12.8,6.5)); fig.patch.set_facecolor("white")
        for i,(metric,label) in enumerate(panels): plot_panel(ax.flat[i],d,k,metric,label,title)
        fig.suptitle(title,fontsize=12,y=.995)
        fig.tight_layout(rect=(0,0,1,.96)); fig.savefig(OUT/path,dpi=300); plt.close(fig)
    rail_title="Rail model-selection diagnostics (n=403); red marker indicates adopted K=5. Panels use independent y-axes."
    bus_title="Bus model-selection diagnostics (n=3,383); red marker indicates adopted K=4. Panels use independent y-axes."
    six_panel(rb,5,rail_title,"Appendix_candidate_rail_k_selection_diagnostics.png")
    six_panel(bk,4,bus_title,"Appendix_candidate_bus_k_selection_diagnostics.png")
    fig,ax=plt.subplots(4,3,figsize=(12.8,10.48)); fig.patch.set_facecolor("white")
    for i,(metric,label) in enumerate(panels): plot_panel(ax.flat[i],rb,5,metric,label,"Rail")
    for i,(metric,label) in enumerate(panels): plot_panel(ax.flat[6+i],bk,4,metric,label,"Bus")
    fig.suptitle(rail_title,fontsize=10.5,y=.995)
    fig.text(.5,.499,bus_title,ha="center",va="center",fontsize=10,weight="bold")
    fig.tight_layout(rect=(0,0,1,.985),h_pad=2.2)
    fig.savefig(OUT/"Figure_4_1_k_selection_and_stability.png",dpi=300)
    plt.close(fig)

LNWC_COLOURS = {
    1: "#E78AC3", 2: "#FFD92F", 3: "#8DA0CB", 4: "#66C2A5",
    5: "#FC8D62", 6: "#A6D854", 7: "#E5C494",
}

def cluster_lnwc_maps():
    """Presentation-styled twin of analysis/03_lnwc_context/src/run_lnwc_analysis.py's
    two combined map figures (rail catchments+clusters/LNWC, bus clusters/LNWC).
    Reads that pipeline's already-computed outputs (catchment geometries,
    station/LSOA-level cluster+LNWC assignments) rather than recomputing the
    Voronoi catchments or LNWC spatial joins -- same numbers, clearer styling."""
    base=gpd.read_file(BOUNDARY).to_crs(4326)

    # --- Rail: catchments + station points, cluster and dominant-LNWC panels ---
    catch=gpd.read_file(RQ2/"spatial"/"rail_catchments_800m_allmodes.geojson")
    rail_stations=pd.read_csv(RQ2/"data"/"rail_analysis_station.csv")
    catch=catch.merge(rail_stations[["NLC","dominant_lnwc"]],on="NLC",how="left")
    stations=gpd.GeoDataFrame(rail_stations,geometry=gpd.points_from_xy(rail_stations.lon,rail_stations.lat),crs=4326)
    rail_names=pd.read_csv(RAIL/"rail_cluster_names.csv").set_index("cluster")

    fig,axes=plt.subplots(1,2,figsize=(16,8.2))
    for ax in axes: base.boundary.plot(ax=ax,color="#D5D5D5",linewidth=.2)
    for c in range(5):
        catch[catch.cluster==c].plot(ax=axes[0],color=RC[c],linewidth=.2,edgecolor="white")
        stations[stations.cluster==c].plot(ax=axes[0],color=RC[c],markersize=12,edgecolor="white",linewidth=.4)
    handles0=[Patch(facecolor=RC[c],edgecolor="none",label=f"C{c} {rail_names.loc[c,'short']}") for c in range(5)]
    axes[0].legend(handles=handles0,loc="lower left",fontsize=8.5,title="Rail cluster",title_fontsize=9.5,frameon=True)
    axes[0].set_title("Rail clusters + 800 m catchments\n(K=5, all-modes, NaPTAN-matched)",fontsize=13,weight="bold")

    for g in range(1,8):
        sub=catch[catch.dominant_lnwc==g]
        if len(sub): sub.plot(ax=axes[1],color=LNWC_COLOURS[g],linewidth=.2,edgecolor="white")
    handles1=[Patch(facecolor=LNWC_COLOURS[g],edgecolor="none",label=f"LNWC {g}") for g in range(1,8)]
    axes[1].legend(handles=handles1,loc="lower left",fontsize=8.5,title="Dominant LNWC group",title_fontsize=9.5,frameon=True)
    axes[1].set_title("Dominant LNWC group within each rail catchment",fontsize=13,weight="bold")
    for ax in axes: ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT/"rail_clusters_lnwc_map.png",dpi=300,bbox_inches="tight")
    plt.close(fig)

    # --- Bus: LSOA choropleth, cluster and LNWC panels ---
    bus=pd.read_csv(RQ2/"data"/"bus_analysis_lsoa.csv")
    bus_names=pd.read_csv(BUSROOT/"data"/"bus_cluster_names.csv").set_index("cluster")
    g=base.merge(bus[["lsoa21cd","cluster","lnc_grp"]],left_on="LSOA21CD",right_on="lsoa21cd",how="left")

    fig,axes=plt.subplots(1,2,figsize=(16,8.2))
    g[g.cluster.isna()].plot(ax=axes[0],color="#EEEEEE",linewidth=0)
    for c in range(4):
        g[g.cluster==c].plot(ax=axes[0],color=BC[c],linewidth=0)
    handles2=[Patch(facecolor=BC[c],edgecolor="none",label=f"C{c} {bus_names.loc[c,'short']}") for c in range(4)]
    handles2.append(Patch(facecolor="#EEEEEE",edgecolor="none",label="No data"))
    axes[0].legend(handles=handles2,loc="lower left",fontsize=8.5,title="Bus cluster",title_fontsize=9.5,frameon=True)
    axes[0].set_title("Bus clusters\n(K=4, StopArea CLR)",fontsize=13,weight="bold")

    g[g.lnc_grp.isna()].plot(ax=axes[1],color="#EEEEEE",linewidth=0)
    for lg in range(1,8):
        g[g.lnc_grp==lg].plot(ax=axes[1],color=LNWC_COLOURS[lg],linewidth=0)
    handles3=[Patch(facecolor=LNWC_COLOURS[lg],edgecolor="none",label=f"LNWC {lg}") for lg in range(1,8)]
    handles3.append(Patch(facecolor="#EEEEEE",edgecolor="none",label="No data"))
    axes[1].legend(handles=handles3,loc="lower left",fontsize=8.5,title="LNWC group",title_fontsize=9.5,frameon=True)
    axes[1].set_title("LNWC groups in the bus analysis universe",fontsize=13,weight="bold")
    for ax in axes: ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(OUT/"bus_clusters_lnwc_map.png",dpi=300,bbox_inches="tight")
    plt.close(fig)

def maps(rl,rn,bl,bn):
    base=gpd.read_file(BOUNDARY).to_crs(27700)
    for mode,labs,names,pal in [("rail",rl,rn,RC),("bus",bl,bn,BC)]:
      fig,ax=plt.subplots(figsize=(7,7)); base.plot(ax=ax,color="#F2F2F2",edgecolor="white",linewidth=.1)
      if mode=="rail":
        pts=pd.read_csv(RAIL_COORDS).rename(columns={"unit":"id"}); pts.id=pts.id.astype(str); g=gpd.GeoDataFrame(labs.assign(id=labs.id.astype(str)).merge(pts[["id","easting","northing"]],on="id"),geometry=gpd.points_from_xy(pts.set_index('id').loc[labs.id.astype(str),'easting'],pts.set_index('id').loc[labs.id.astype(str),'northing']),crs=27700)
        for c in range(5): g[g.cluster==c].plot(ax=ax,color=pal[c],markersize=22,edgecolor="white",linewidth=.35,label=f"C{c} {names.loc[c,'short']}")
      else:
        # Retain the original three-state map grammar: 414 input LSOAs below
        # the current threshold are grey; polygons with no input unit remain a
        # lighter background state instead of being implied to be clustered.
        all_bus=pd.read_csv(BUSROOT / "clr" / "labels" / "k4_labels.csv").rename(columns={"lsoa":"LSOA21CD"})
        g=base.merge(all_bus[["LSOA21CD","retained_for_fit","cluster"]],on="LSOA21CD",how="left")
        g[g.retained_for_fit.isna()].plot(ax=ax,color="#F2F2F2",edgecolor="white",linewidth=.04)
        g[g.retained_for_fit.eq(False)].plot(ax=ax,color="#A7A9AC",edgecolor="white",linewidth=.04)
        for c in range(4): g[g.retained_for_fit.eq(True)&g.cluster.eq(c)].plot(ax=ax,color=pal[c],edgecolor="white",linewidth=.04)
      handles=[Patch(facecolor=pal[c], edgecolor="none", label=f"C{c} {names.loc[c,'short']}") for c in range(len(names))]
      if mode=="bus": handles.append(Patch(facecolor="#A7A9AC",edgecolor="none",label="Below threshold: not fitted (n=414)"))
      ax.set_axis_off(); ax.legend(handles=handles,loc="lower left",fontsize=7,frameon=True,title=f"{mode.title()} cluster"); ax.set_title(f"{mode.title()} cluster map: {'station points' if mode=='rail' else 'LSOA polygons'}")
      fig.tight_layout(); fig.savefig(OUT/f"Figure_4_{'3' if mode=='rail' else '5'}_{mode}_map.png",dpi=260); plt.close(fig)

def main():
    rl,rn,bl,bn=write_tables(); temporal("rail",rl,rn); temporal("bus",bl,bn); temporal_by_cluster_rail(rl,rn); temporal_by_cluster_bus(bl,bn); heatmap("rail"); heatmap("bus"); context("rail"); context("bus"); context_full_matrix("rail"); context_full_matrix("bus"); context_heatmap("rail"); context_heatmap("bus"); behavioural_effect_ranking_combined(); night_behaviour_z("rail"); night_behaviour_z("bus"); kselection(); cluster_lnwc_maps(); maps(rl,rn,bl,bn)
    (OUT/"generation_manifest.json").write_text(json.dumps({"rail_n":len(rl),"bus_n":len(bl),"rail_k":5,"bus_k":4,"script":str(Path(__file__).resolve())},indent=2),encoding="utf-8")
if __name__=="__main__": main()
