import sqlite3
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "kuyumcu.db"
st.set_page_config(page_title="Kuyumcu Kâr Takibi", page_icon="💰", layout="wide")

DEFAULT_PRODUCTS = [
    ("Yeni Çeyrek","Altın","adet",1.62), ("Eski Çeyrek","Altın","adet",1.62),
    ("Yeni Yarım","Altın","adet",3.24), ("Eski Yarım","Altın","adet",3.24),
    ("Yeni Tam","Altın","adet",6.48), ("Eski Tam","Altın","adet",6.48),
    ("Ata","Altın","adet",6.613), ("Gremse","Altın","adet",16.20),
    ("24 Ayar Gram","Gram","gram",1.0), ("22 Ayar Gram","Gram Sabit","adet",0.0),
    ("Gümüş Takı","Gümüş","gram",0.0),
    ("İnce Bilezik","Bilezik","gram",0.925), ("Kalın Bilezik","Bilezik","gram",0.935),
    ("14 Ayar Kolye","14 Ayar","gram",0.695), ("14 Ayar Bilezik","14 Ayar","gram",0.695),
    ("14 Ayar Yüzük","14 Ayar","gram",0.695), ("14 Ayar Diğer Fantazi","14 Ayar","gram",0.695),
    ("22 Ayar Kolye","22 Ayar","gram",1.026), ("22 Ayar Bilezik","22 Ayar","gram",1.026),
    ("22 Ayar Yüzük","22 Ayar","gram",1.026), ("22 Ayar Diğer Fantazi","22 Ayar","gram",1.026),
    ("14 Ayar Temiz Kolye","Temiz 14 Ayar","temiz",0.600),
    ("14 Ayar Temiz Bilezik","Temiz 14 Ayar","temiz",0.600),
    ("14 Ayar Temiz Yüzük","Temiz 14 Ayar","temiz",0.600),
    ("14 Ayar Temiz Diğer","Temiz 14 Ayar","temiz",0.600),
    ("22 Ayar Temiz Kolye","Temiz 22 Ayar","temiz",0.910),
    ("22 Ayar Temiz Bilezik","Temiz 22 Ayar","temiz",0.910),
    ("22 Ayar Temiz Yüzük","Temiz 22 Ayar","temiz",0.910),
    ("22 Ayar Temiz Diğer","Temiz 22 Ayar","temiz",0.910),
]

def db():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; return c

def init_db():
    c=db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT UNIQUE,category TEXT,operation TEXT,coefficient REAL);
    CREATE TABLE IF NOT EXISTS transactions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,tx_date TEXT,tx_type TEXT,product_id INTEGER,product_name TEXT,
      category TEXT,quantity REAL,grams REAL,has_price REAL,customer_amount REAL,cost_amount REAL,
      profit_tl REAL,profit_gram REAL,notes TEXT);
    """)
    for k,v in [("scrap_buy_coeff",.91),("scrap_sell_coeff",.93)]:
        c.execute("INSERT OR IGNORE INTO settings VALUES(?,?)",(k,v))
    for p in DEFAULT_PRODUCTS:
        c.execute("INSERT OR IGNORE INTO products(name,category,operation,coefficient) VALUES(?,?,?,?)",p)
    c.commit(); c.close()

def products():
    c=db(); d=pd.read_sql_query("SELECT * FROM products ORDER BY category,name",c); c.close(); return d

def get_tx(txid):
    c=db(); r=c.execute("SELECT * FROM transactions WHERE id=?",(txid,)).fetchone(); c.close(); return r

def transactions(start=None,end=None):
    c=db(); q="SELECT * FROM transactions WHERE 1=1"; p=[]
    if start: q+=" AND tx_date>=?"; p.append(str(start))
    if end: q+=" AND tx_date<=?"; p.append(str(end))
    q+=" ORDER BY tx_date DESC,id DESC"
    d=pd.read_sql_query(q,c,params=p); c.close(); return d

def add_tx(row):
    c=db()
    c.execute("""INSERT INTO transactions
    (tx_date,tx_type,product_id,product_name,category,quantity,grams,has_price,customer_amount,cost_amount,profit_tl,profit_gram,notes)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",row)
    c.commit(); c.close()

def delete_tx(txid):
    c=db(); c.execute("DELETE FROM transactions WHERE id=?",(txid,)); c.commit(); c.close()

def update_tx(txid,row):
    c=db()
    c.execute("""UPDATE transactions SET
      tx_date=?,tx_type=?,product_id=?,product_name=?,category=?,quantity=?,grams=?,
      has_price=?,customer_amount=?,cost_amount=?,profit_tl=?,profit_gram=?,notes=?
      WHERE id=?""",(*row,txid))
    c.commit(); c.close()

def money(x):
    return f"{x:,.2f} TL".replace(",","X").replace(".",",").replace("X",".")

init_db()
st.title("💰 Kuyumcu Kâr Takibi")
st.caption("Satış • Alış • Günlük kayıt • Düzenle • Sil")

with st.sidebar:
    st.header("Gün")
    selected_date=st.date_input("Tarih",date.today())
    has=st.number_input("Has altın fiyatı (TL/gr)",min_value=0.,step=10.,format="%.2f")
    st.header("Hurda bilezik")
    scrap_buy=st.number_input("Alış katsayısı",min_value=0.,value=.91,step=.001,format="%.3f")
    scrap_sell=st.number_input("Satış katsayısı",min_value=0.,value=.93,step=.001,format="%.3f")
    st.header("Sabit kurallar")
    st.write("22 ayar gram: **100 TL/adet**")
    st.write("Gümüş takı satış: **100 TL/gram**")

day=transactions(selected_date,selected_date)
sales=day.loc[day.tx_type=="Satış","profit_tl"].sum() if not day.empty else 0
buys=day.loc[day.tx_type=="Alış","profit_tl"].sum() if not day.empty else 0
total=day.profit_tl.sum() if not day.empty else 0
gram=day.profit_gram.sum() if not day.empty else 0
a,b,c,d=st.columns(4)
a.metric("Satış kârı",money(sales)); b.metric("Alış kârı",money(buys))
c.metric("Toplam kâr",money(total)); d.metric("Has karşılığı",f"{gram:.4f} gr")

ts,tb,th,tc=st.tabs(["🟢 Satış","🔵 Alış","📊 Kayıtlar","⚙️ Maliyetler"])
pdf=products()

def needs_grams(p):
    return p["operation"] in ("gram","temiz") or p["category"] in ("Bilezik","14 Ayar","22 Ayar","Temiz 14 Ayar","Temiz 22 Ayar","Gümüş")

def calc_sale(name,p,qty,grams,amount,has):
    if name=="22 Ayar Gram":
        profit=100*qty; cost=amount-profit
    elif name=="Gümüş Takı":
        profit=100*grams; cost=amount-profit
    else:
        basis=grams if needs_grams(p) else qty
        cost=has*p.coefficient*basis; profit=amount-cost
    return cost,profit

def calc_buy(name,p,typ,qty,grams,paid,has):
    if typ=="Hurda bilezik":
        cost=grams*has*scrap_buy; profit=grams*has*(scrap_sell-scrap_buy); pid=None; cat="Bilezik / Hurda"
    elif name=="22 Ayar Gram":
        profit=100*qty; cost=paid+profit; pid=int(p.id); cat="Gram Sabit"
    else:
        basis=grams if needs_grams(p) else qty
        cost=has*p.coefficient*basis; profit=cost-paid; pid=int(p.id); cat=p.category
    return cost,profit,pid,cat

with ts:
    st.subheader("Satış")
    with st.form("sale"):
        name=st.selectbox("Ürün",pdf.name.tolist())
        p=pdf[pdf.name==name].iloc[0]
        qty=st.number_input("Adet",min_value=1.,value=1.,step=1.)
        grams=st.number_input("Gram",min_value=0.,value=0.,step=.01,format="%.2f") if needs_grams(p) else 0.
        amount=st.number_input("Müşteriden alınan toplam tutar (TL)",min_value=0.,value=0.,step=100.,format="%.2f")
        note=st.text_input("Not")
        ok=st.form_submit_button("Satışı Kaydet",type="primary")
    if ok:
        if amount<=0: st.error("Satış tutarını gir.")
        elif name!="Gümüş Takı" and has<=0: st.error("Has altın fiyatını gir.")
        elif needs_grams(p) and grams<=0: st.error("Gram bilgisini gir.")
        else:
            cost,profit=calc_sale(name,p,qty,grams,amount,has)
            add_tx((str(selected_date),"Satış",int(p.id),name,p.category,qty,grams,has,amount,cost,profit,profit/has if has else 0,note))
            st.success(f"Satış kaydedildi. Kâr: {money(profit)}")

with tb:
    st.subheader("Alış")
    st.info("Alış kârı = normal toptancı maliyeti − müşteriye verdiğimiz gerçek tutar.")
    typ=st.radio("Alış türü",["Standart ürün","Temiz ürün","Hurda bilezik"],horizontal=True)
    with st.form("buy"):
        if typ=="Standart ürün":
            choices=pdf[~pdf.name.str.contains("Temiz")].copy()
            name=st.selectbox("Ürün",choices.name.tolist()); p=choices[choices.name==name].iloc[0]
            qty=st.number_input("Adet",min_value=1.,value=1.,step=1.)
            grams=st.number_input("Gram",min_value=0.,value=0.,step=.01,format="%.2f") if needs_grams(p) else 0.
        elif typ=="Temiz ürün":
            choices=pdf[pdf.name.str.contains("Temiz")].copy()
            name=st.selectbox("Ürün",choices.name.tolist()); p=choices[choices.name==name].iloc[0]
            qty=st.number_input("Adet",min_value=1.,value=1.,step=1.)
            grams=st.number_input("Gram",min_value=0.,value=0.,step=.01,format="%.2f")
        else:
            name="Hurda Bilezik"; p=None; qty=1.; grams=st.number_input("Hurda bilezik gramı",min_value=0.,value=0.,step=.01,format="%.2f")
        paid=st.number_input("Müşteriye verdiğimiz toplam tutar (TL)",min_value=0.,value=0.,step=100.,format="%.2f")
        note=st.text_input("Not")
        ok=st.form_submit_button("Alışı Kaydet",type="primary")
    if ok:
        if has<=0: st.error("Has altın fiyatını gir.")
        elif paid<=0: st.error("Müşteriye verdiğimiz tutarı gir.")
        elif typ=="Hurda bilezik" and grams<=0: st.error("Hurda gramını gir.")
        elif typ!="Hurda bilezik" and needs_grams(p) and grams<=0: st.error("Gram bilgisini gir.")
        else:
            cost,profit,pid,cat=calc_buy(name,p,typ,qty,grams,paid,has)
            add_tx((str(selected_date),"Alış",pid,name,cat,qty,grams,has,paid,cost,profit,profit/has if has else 0,note))
            st.success(f"Alış kaydedildi. Normal maliyet: {money(cost)} | Kâr: {money(profit)}")

with th:
    st.subheader("Kayıtlar")
    x,y=st.columns(2)
    start=x.date_input("Başlangıç",selected_date); end=y.date_input("Bitiş",selected_date)
    h=transactions(start,end)
    if h.empty: st.info("Kayıt yok.")
    else:
        for _,r in h.iterrows():
            label=f"#{int(r.id)} • {r.tx_date} • {r.tx_type} • {r.product_name} • Kâr: {money(r.profit_tl)}"
            with st.expander(label):
                q1,q2,q3,q4=st.columns(4)
                q1.write(f"Adet: **{r.quantity:g}**")
                q2.write(f"Gram: **{r.grams:g}**")
                q3.write(f"Has: **{r.has_price:,.2f} TL**")
                q4.write(f"Tutar: **{r.customer_amount:,.2f} TL**")
                st.write(f"Normal maliyet: **{money(r.cost_amount)}**")
                st.write(f"Has karşılığı kâr: **{r.profit_gram:.4f} gr**")
                if r.notes: st.write(f"Not: {r.notes}")
                ec,dc=st.columns(2)
                if ec.button("✏️ Düzenle",key=f"edit_{r.id}"):
                    st.session_state[f"editing_{r.id}"]=True
                    st.rerun()
                if dc.button("🗑️ Sil",key=f"delete_{r.id}"):
                    st.session_state[f"confirm_delete_{r.id}"]=True
                    st.rerun()

                if st.session_state.get(f"confirm_delete_{r.id}",False):
                    st.warning("Bu kayıt kalıcı olarak silinecek.")
                    yc,nc=st.columns(2)
                    if yc.button("Evet, sil",key=f"yes_{r.id}",type="primary"):
                        delete_tx(int(r.id))
                        st.session_state.pop(f"confirm_delete_{r.id}",None)
                        st.success("Kayıt silindi.")
                        st.rerun()
                    if nc.button("Vazgeç",key=f"no_{r.id}"):
                        st.session_state.pop(f"confirm_delete_{r.id}",None)
                        st.rerun()

                if st.session_state.get(f"editing_{r.id}",False):
                    st.markdown("### Kaydı düzenle")
                    edate=st.date_input("Tarih",date.fromisoformat(r.tx_date),key=f"edate_{r.id}")
                    ename=st.selectbox("Ürün",pdf.name.tolist(),index=pdf.name.tolist().index(r.product_name),key=f"ename_{r.id}")
                    ep=pdf[pdf.name==ename].iloc[0]
                    etype=r.tx_type
                    eqty=st.number_input("Adet",min_value=.0,value=float(r.quantity),step=1.,key=f"eqty_{r.id}")
                    egrams=st.number_input("Gram",min_value=.0,value=float(r.grams),step=.01,format="%.2f",key=f"egrams_{r.id}")
                    ehas=st.number_input("Has altın fiyatı",min_value=.0,value=float(r.has_price),step=10.,format="%.2f",key=f"ehas_{r.id}")
                    eamount=st.number_input("Müşteri tutarı",min_value=.0,value=float(r.customer_amount),step=100.,format="%.2f",key=f"eamount_{r.id}")
                    enote=st.text_input("Not",value=str(r.notes or ""),key=f"enote_{r.id}")
                    save,cancel=st.columns(2)
                    if save.button("💾 Değişiklikleri Kaydet",key=f"save_{r.id}",type="primary"):
                        if etype=="Satış":
                            cost,profit=calc_sale(ename,ep,eqty,egrams,eamount,ehas)
                        else:
                            typ2="Hurda bilezik" if ename=="Hurda Bilezik" else ("Temiz ürün" if "Temiz" in ename else "Standart ürün")
                            cost,profit,pid,cat=calc_buy(ename,ep,typ2,eqty,egrams,eamount,ehas)
                        pid=int(ep.id)
                        cat=ep.category
                        update_tx(int(r.id),(str(edate),etype,pid,ename,cat,eqty,egrams,ehas,eamount,cost,profit,profit/ehas if ehas else 0,enote))
                        st.session_state.pop(f"editing_{r.id}",None)
                        st.success("Kayıt güncellendi.")
                        st.rerun()
                    if cancel.button("İptal",key=f"cancel_{r.id}"):
                        st.session_state.pop(f"editing_{r.id}",None)
                        st.rerun()

with tc:
    st.subheader("Maliyet katsayıları")
    st.caption("Örn. çeyrek 1,62 ise: 6.730 × 1,62 = 10.902,60 TL normal maliyet.")
    e=st.data_editor(pdf[["id","name","category","operation","coefficient"]],use_container_width=True,hide_index=True)
    if st.button("Katsayıları Kaydet"):
        c=db()
        for _,r in e.iterrows():
            c.execute("UPDATE products SET coefficient=? WHERE id=?",(float(r.coefficient),int(r.id)))
        c.commit(); c.close(); st.success("Katsayılar kaydedildi.")
