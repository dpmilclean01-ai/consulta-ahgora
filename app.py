import re
import html
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Consulta de Chave - Ahgora",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================
# ESTILO VISUAL (MOBILE)
# =========================
st.markdown("""
<style>
    .block-container {
        max-width: 700px;
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .main-title {
        font-size: 1.9rem;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 0.3rem;
        text-align: center;
    }

    .sub-title {
        font-size: 1rem;
        color: #555;
        text-align: center;
        margin-bottom: 1.2rem;
    }

    .info-box {
        background: #f7f7f7;
        border: 1px solid #e4e4e4;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 14px;
    }

    .label-text {
        font-size: 0.9rem;
        color: #555;
        margin-bottom: 4px;
    }

    .value-text {
        font-size: 1.15rem;
        font-weight: 700;
        word-break: break-word;
    }

    .small-help {
        font-size: 0.92rem;
        color: #666;
        margin-top: 6px;
    }

    .stTextInput > div > div > input {
        font-size: 1.2rem !important;
        text-align: center;
        padding: 0.85rem !important;
        border-radius: 12px !important;
    }

    .copy-row {
        margin-top: 8px;
        margin-bottom: 14px;
    }

    .copy-btn {
        width: 100%;
        border: none;
        border-radius: 12px;
        padding: 12px 14px;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
        background: #111827;
        color: white;
    }

    .copy-btn:hover {
        opacity: 0.92;
    }

    .copy-btn:active {
        transform: scale(0.99);
    }

    .countdown-box {
        margin-top: 10px;
        padding: 12px;
        border-radius: 12px;
        background: #fff8e1;
        border: 1px solid #ffe08a;
        text-align: center;
        font-weight: 600;
    }

    .footer-note {
        margin-top: 18px;
        text-align: center;
        color: #666;
        font-size: 0.88rem;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# FUNÇÕES
# =========================
def somente_digitos(texto):
    return re.sub(r"\D", "", str(texto or ""))

def formatar_cpf(cpf):
    cpf = somente_digitos(cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

@st.cache_data
def carregar_base():
    """
    Carrega dados.xlsx.
    Se não existir, tenta dados.csv.
    Padroniza colunas e CPF.
    """
    try:
        df = pd.read_excel("dados.xlsx", dtype=str)
    except FileNotFoundError:
        df = pd.read_csv("dados.csv", dtype=str)

    df.columns = [str(col).strip().upper() for col in df.columns]

    colunas_necessarias = ["CPF", "NOME", "MATRICULA", "CHAVE"]
    faltando = [c for c in colunas_necessarias if c not in df.columns]
    if faltando:
        raise ValueError(
            f"Colunas ausentes na planilha: {', '.join(faltando)}. "
            f"As colunas obrigatórias são: CPF, NOME, MATRICULA, CHAVE."
        )

    for col in colunas_necessarias:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["CPF_LIMPO"] = df["CPF"].apply(somente_digitos)
    df = df[df["CPF_LIMPO"].str.len() == 11].copy()

    # Remove duplicidade de CPF, mantendo a primeira ocorrência
    df = df.drop_duplicates(subset="CPF_LIMPO", keep="first")

    return df

def botao_copiar(texto, rotulo_botao="Copiar"):
    """
    Cria um botão HTML/JS para copiar texto.
    """
    texto_js = html.escape(str(texto)).replace("'", "\\'")
    rotulo_js = html.escape(rotulo_botao).replace("'", "\\'")

    components.html(
        f"""
        <div class="copy-row">
            <button class="copy-btn" onclick="copiarTexto()">{rotulo_js}</button>
        </div>

        <script>
        async function copiarTexto() {{
            const texto = '{texto_js}';
            try {{
                await navigator.clipboard.writeText(texto);
                const btn = document.querySelector('.copy-btn');
                const original = btn.innerText;
                btn.innerText = 'Copiado!';
                setTimeout(() => {{
                    btn.innerText = original;
                }}, 1800);
            }} catch (e) {{
                alert('Não foi possível copiar automaticamente. Texto: ' + texto);
            }}
        }}
        </script>
        """,
        height=70,
    )

def iniciar_reset_automatico(segundos=40):
    """
    Recarrega a página após X segundos.
    """
    components.html(
        f"""
        <div class="countdown-box">
            Esta consulta será limpa automaticamente em <span id="contador">{segundos}</span> segundos.
        </div>

        <script>
            let segundos = {segundos};
            const contador = document.getElementById("contador");

            const intervalo = setInterval(() => {{
                segundos -= 1;
                if (contador) {{
                    contador.textContent = segundos;
                }}

                if (segundos <= 0) {{
                    clearInterval(intervalo);
                    window.parent.location.reload();
                }}
            }}, 1000);
        </script>
        """,
        height=80,
    )

# =========================
# CABEÇALHO
# =========================
st.markdown('<div class="main-title">Consulta de Chave de Ativação</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Digite seu CPF para visualizar sua matrícula e sua chave do Ahgora.</div>',
    unsafe_allow_html=True
)

with st.container():
    st.markdown("""
    <div class="info-box">
        <div style="font-weight:700; margin-bottom:8px;">Como usar</div>
        <div>1. Digite seu CPF</div>
        <div>2. Confira seus dados</div>
        <div>3. Copie a matrícula e a chave</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# CARREGAR BASE
# =========================
try:
    df = carregar_base()
except Exception as e:
    st.error(f"Erro ao carregar a base: {e}")
    st.stop()

# =========================
# ENTRADA DO CPF
# =========================
if "cpf_input" not in st.session_state:
    st.session_state.cpf_input = ""

def ao_digitar_cpf():
    bruto = st.session_state.cpf_input
    digitos = somente_digitos(bruto)[:11]
    st.session_state.cpf_input = formatar_cpf(digitos) if len(digitos) == 11 else digitos

st.text_input(
    "CPF",
    key="cpf_input",
    placeholder="Digite seu CPF",
    on_change=ao_digitar_cpf,
    help="Pode digitar com ou sem pontos e traço."
)

cpf_digitado = somente_digitos(st.session_state.cpf_input)

# Formatação enquanto a pessoa digita/pasta conteúdo
if st.session_state.cpf_input:
    cpf_mascarado = formatar_cpf(cpf_digitado) if len(cpf_digitado) <= 11 else formatar_cpf(cpf_digitado[:11])
    if st.session_state.cpf_input != cpf_mascarado and len(cpf_digitado) <= 11:
        st.session_state.cpf_input = cpf_mascarado
        st.rerun()

# =========================
# VALIDAÇÃO / CONSULTA
# =========================
if st.session_state.cpf_input:
    if len(cpf_digitado) < 11:
        st.warning("Digite os 11 números do CPF para consultar.")
        st.stop()

    if len(cpf_digitado) > 11:
        st.error("CPF inválido.")
        st.stop()

    resultado = df[df["CPF_LIMPO"] == cpf_digitado]

    if resultado.empty:
        st.error("CPF não encontrado.")
        st.stop()

    linha = resultado.iloc[0]

    st.success("Dados localizados com sucesso.")

    st.markdown(f"""
    <div class="info-box">
        <div class="label-text">Nome</div>
        <div class="value-text">{html.escape(str(linha["NOME"]))}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
        <div class="label-text">Matrícula</div>
        <div class="value-text">{html.escape(str(linha["MATRICULA"]))}</div>
    </div>
    """, unsafe_allow_html=True)
    botao_copiar(str(linha["MATRICULA"]), "Copiar matrícula")

    st.markdown(f"""
    <div class="info-box">
        <div class="label-text">Chave de ativação</div>
        <div class="value-text">{html.escape(str(linha["CHAVE"]))}</div>
    </div>
    """, unsafe_allow_html=True)
    botao_copiar(str(linha["CHAVE"]), "Copiar chave")

    iniciar_reset_automatico(40)

st.markdown(
    '<div class="footer-note">Após 40 segundos, a consulta será limpa automaticamente.</div>',
    unsafe_allow_html=True
)