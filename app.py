import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import plotly.express as px
from datetime import datetime
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="Agri-Suivi Pro", page_icon="🌾", layout="wide")

# --- DONNÉES PAYS & VALIDATION ---
PAYS_DATA = {
    "Cameroun": {"code": "+237", "regex": r"^\d{9}$"},
    "France": {"code": "+33", "regex": r"^\d{9}$"},
    "Côte d'Ivoire": {"code": "+225", "regex": r"^\d{10}$"},
    "Sénégal": {"code": "+221", "regex": r"^\d{9}$"},
    "Canada": {"code": "+1", "regex": r"^\d{10}$"}
}

# --- BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('agri_suivi_v1.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, nom TEXT, prenom TEXT, 
                phone TEXT, password TEXT, sex TEXT, pays TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS recoltes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, date TEXT, 
                culture TEXT, quantite REAL, prix_vente REAL, parcelle TEXT,
                engrais_utilise TEXT, main_d_oeuvre REAL, statut_stock TEXT,
                date_recolte TEXT, notes TEXT)''')
    conn.commit()
    return conn, c

conn, c = init_db()

def hash_pwd(pwd): return hashlib.sha256(str.encode(pwd)).hexdigest()

# --- GESTION DE LA SESSION ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

def main():
    if not st.session_state.auth:
        st.title("🌾 Agri-Suivi : Votre Gestionnaire Agricole")
        tab_login, tab_signup = st.tabs(["Se Connecter", "S'inscrire"])

        with tab_signup:
            with st.form("inscription_form"):
                col1, col2 = st.columns(2)
                with col1:
                    s_nom, s_pre = st.text_input("Nom"), st.text_input("Prénom")
                    s_em, s_sex = st.text_input("Email"), st.selectbox("Sexe", ["Masculin", "Féminin"])
                with col2:
                    s_pa = st.selectbox("Nationalité", list(PAYS_DATA.keys()))
                    st.info(f"Indicatif pays : {PAYS_DATA[s_pa]['code']}")
                    s_ph = st.text_input("Numéro de téléphone (sans indicatif)")
                    s_pw = st.text_input("Mot de passe", type='password')
                
                if st.form_submit_button("Créer mon compte"):
                    if re.match(PAYS_DATA[s_pa]["regex"], s_ph):
                        try:
                            c.execute('INSERT INTO users VALUES (?,?,?,?,?,?,?)', 
                                     (s_em, s_nom, s_pre, f"{PAYS_DATA[s_pa]['code']} {s_ph}", hash_pwd(s_pw), s_sex, s_pa))
                            conn.commit()
                            st.success("🎉 Compte créé avec succès ! Cliquez sur 'Se Connecter' pour continuer.")
                        except: st.error("Cet email est déjà utilisé.")
                    else: st.error(f"Le format du numéro est invalide pour le {s_pa}.")

        with tab_login:
            with st.form("connexion_form"):
                l_nom, l_pre = st.text_input("Nom"), st.text_input("Prénom")
                l_pw = st.text_input("Mot de passe", type='password')
                if st.form_submit_button("Se connecter"):
                    c.execute('SELECT * FROM users WHERE nom=? AND prenom=? AND password=?', (l_nom, l_pre, hash_pwd(l_pw)))
                    user = c.fetchone()
                    if user:
                        st.session_state.auth, st.session_state.user = True, list(user)
                        st.rerun()
                    else: st.error("Identifiants incorrects.")

    else:
        # --- INTERFACE PRINCIPALE ---
        u_email = st.session_state.user[0]
        st.sidebar.title("🚀 KERIANE")
        st.sidebar.caption("Agri-Suivi (Suivi de Projets & Productivité)")
        
        menu = st.sidebar.selectbox("Menu", ["Collecte de Données", "Mon Profil", "Déconnexion"])

        if menu == "Déconnexion":
            st.session_state.auth = False
            st.rerun()

        elif menu == "Mon Profil":
            st.header("👤 Modifier mon Profil")
            with st.form("profil_edit"):
                n_nom = st.text_input("Nom", value=st.session_state.user[1])
                n_em = st.text_input("Email", value=st.session_state.user[0])
                n_ph = st.text_input("Téléphone", value=st.session_state.user[3])
                if st.form_submit_button("Sauvegarder les modifications"):
                    c.execute('UPDATE users SET nom=?, email=?, phone=? WHERE email=?', (n_nom, n_em, n_ph, u_email))
                    conn.commit()
                    st.success("Profil mis à jour !")

        elif menu == "Collecte de Données":
            t_saisie, t_analyse, t_gestion = st.tabs(["📥 Saisie", "🥧 Analyse", "🛠️ Gestion"])

            with t_saisie:
                with st.form("saisie_recolte"):
                    culture = st.selectbox("Type de Culture", ["Maïs", "Manioc", "Café", "Cacao", "Tomate", "AUTRE"])
                    culture_c = st.text_input("Si AUTRE, précisez")
                    cult_final = culture_c if culture == "AUTRE" else culture
                    
                    c1, c2 = st.columns(2)
                    quant = c1.number_input("Quantité récoltée (kg)", min_value=0.0, value=1.0)
                    prix = c2.number_input("Prix de vente estimé (FCFA/kg)", min_value=0.0)
                    
                    st.subheader("Paramètres de Production")
                    c3, c4, c5 = st.columns(3)
                    parcelle = c3.text_input("Nom/Numéro de la Parcelle")
                    engrais = c4.text_input("Engrais/Intrants utilisés")
                    main_d = c5.number_input("Coût Main d'œuvre (FCFA)", min_value=0.0)
                    
                    c6, c7 = st.columns(2)
                    statut = c6.selectbox("Statut du Stock", ["En stock", "Vendu", "Perdu"])
                    date_r = c7.date_input("Date de récolte")
                    
                    notes = st.text_area("Notes additionnelles")
                    
                    if st.form_submit_button("Enregistrer la Récolte"):
                        c.execute('''INSERT INTO recoltes (user_email, date, culture, quantite, prix_vente, parcelle, engrais_utilise, main_d_oeuvre, statut_stock, date_recolte, notes) 
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                                 (u_email, datetime.now().strftime("%d/%m/%Y"), cult_final, float(quant), float(prix), parcelle, engrais, float(main_d), statut, str(date_r), notes))
                        conn.commit()
                        st.success("Donnée agricole enregistrée !")

            with t_analyse:
                c.execute('SELECT culture, quantite FROM recoltes WHERE user_email=?', (u_email,))
                data = c.fetchall()
                if data:
                    df = pd.DataFrame(data, columns=["Culture", "Quantité"])
                    fig = px.pie(df, values='Quantité', names='Culture', hole=0.4, title="Répartition des récoltes")
                    st.plotly_chart(fig, use_container_width=True)
                else: st.info("Aucune donnée disponible pour l'analyse.")

            with t_gestion:
                c.execute('SELECT id, culture, date_recolte FROM recoltes WHERE user_email=?', (u_email,))
                rows = c.fetchall()
                if rows:
                    opt = {f"{r[1]} - {r[2]}": r[0] for r in rows}
                    sel_id = opt[st.selectbox("Choisir une entrée à modifier", list(opt.keys()))]
                    
                    c.execute('SELECT * FROM recoltes WHERE id=?', (sel_id,))
                    curr = c.fetchone()
                    
                    with st.form("modif_form"):
                        st.subheader(f"Modification : {curr[3]}")
                        m_quant = st.number_input("Quantité (kg)", value=float(curr[4]), min_value=0.0)
                        m_prix = st.number_input("Prix (FCFA)", value=float(curr[5]), min_value=0.0)
                        m_statut = st.selectbox("Statut", ["En stock", "Vendu", "Perdu"], index=0)
                        m_notes = st.text_area("Notes", value=curr[11])
                        
                        if st.form_submit_button("Mettre à jour la donnée"):
                            c.execute('UPDATE recoltes SET quantite=?, prix_vente=?, statut_stock=?, notes=? WHERE id=?', 
                                     (float(m_quant), float(m_prix), m_statut, m_notes, sel_id))
                            conn.commit()
                            st.success("Donnée mise à jour !")
                            st.rerun()
                    
                    if st.button("🗑️ Supprimer définitivement"):
                        c.execute('DELETE FROM recoltes WHERE id=?', (sel_id,))
                        conn.commit()
                        st.rerun()

if __name__ == '__main__':
    main()