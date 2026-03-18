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

# =========================================================
# CSS / VISUAL
# =========================================================
st.markdown("""
<style>
    .block-container {
        max-width: 760px;
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    .main-title {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.15;
        text-align: center;
        margin-bottom: 0.35rem;
    }

    .sub-title {
        text-align: center;
        color: #4b5563;
        font-size: 1rem;
        margin-bottom: 1rem;
    }

    .steps-box {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 18px;
    }

    .card-box {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 16px;
        margin-top: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }

    .label-text {
        color: #6b7280;
        font-size: 0.92rem;
        margin-bottom: 4px;
    }

    .value-text {
        color: #111827;
        font-size: 1.18rem;
        font-weight: 800;
        word-break: break-word;
    }

    .stTextInput label {
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    .stTextInput > div > div > input {
        font-size: 1.2rem !important;
        text-align: center;
        padding: 0.95rem !important;
        border-radius: 14px !important;
    }

    .copy-btn-wrap {
        margin-top: 8px;
        margin-bottom: 6px;
    }

    .copy-btn {
        width: 100%;
        background: #111827;
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 12px 14px;
        font-size: 1rem;
        font-weight: 700;
        cursor: pointer;
    }

    .copy-btn:hover {
        opacity: 0.94;
    }

    .countdown-box {
        margin-top: 14px;
        background: #fff7ed;
        border: 1px solid #fdba74;
        border-radius: 14px;
        padding: 12px;
        text-align: center;
        font-weight: 700;
        color: #9a3412;
    }

    .footer-note {
        margin-top: 18px;
        text-align: center;
        font-size: 0.88rem;
        color: #6b7280;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def somente_digitos(texto: str) -> str:
    return re.sub(r"\D", "", str(texto or ""))

def formatar_cpf(cpf: str) -> str:
    cpf = somente_digitos(cpf)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}"

def normalizar_cpf_base(valor: str) -> str:
    """
    Limpa qualquer sujeira e tenta preservar zeros à esquerda.
    Regra:
    - remove tudo que não for número
    - completa com zeros à esquerda até 11
    - mantém apenas os últimos 11 dígitos
    """
    digitos = somente_digitos(valor)
    if not digitos:
        return ""
    return digitos.zfill(11)[-11:]

def normalizar_texto(valor: str) -> str:
    return str(valor or "").strip()

# =========================================================
# CARGA DE DADOS
# =========================================================
@st.cache_data(show_spinner=False)
def carregar_base():
    """
    Lê dados.xlsx (ou dados.csv), padroniza colunas,
    normaliza CPF e cria índice para busca rápida.
    """
    try:
        df = pd.read_excel(
            "dados.xlsx",
            dtype={
                "CPF": str,
                "NOME": str,
                "MATRICULA": str,
                "CHAVE": str
            }
        )
    except FileNotFoundError:
        df = pd.read_csv(
            "dados.csv",
            dtype={
                "CPF": str,
                "NOME": str,
                "MATRICULA": str,
                "CHAVE": str
            }
        )

    df.columns = [str(col).strip().upper() for col in df.columns]

    obrigatorias = ["CPF", "NOME", "MATRICULA", "CHAVE"]
    faltando = [c for c in obrigatorias if c not in df.columns]
    if faltando:
        raise ValueError(
            "Colunas ausentes na planilha: "
            + ", ".join(faltando)
            + ". As colunas obrigatórias são: CPF, NOME, MATRICULA, CHAVE."
        )

    for col in obrigatorias:
        df[col] = df[col].fillna("").astype(str).map(normalizar_texto)

    df["CPF_LIMPO"] = df["CPF"].map(normalizar_cpf_base)
    df = df[df["CPF_LIMPO"].str.len() == 11].copy()

    # remove duplicidade de CPF, mantendo o primeiro
    df = df.drop_duplicates(subset="CPF_LIMPO", keep="first").copy()

    # -----------------------------------------------------
    # OTIMIZAÇÃO DE BUSCA
    # Esta é a parte da busca rápida por CPF:
    # cria um índice em memória para não precisar filtrar
    # o DataFrame inteiro a cada consulta.
    # -----------------------------------------------------
    indice_cpf = {
        row["CPF_LIMPO"]: {
            "NOME": row["NOME"],
            "MATRICULA": row["MATRICULA"],
            "CHAVE": row["CHAVE"],
            "CPF_FORMATADO": formatar_cpf(row["CPF_LIMPO"])
        }
        for _, row in df.iterrows()
    }

    return df, indice_cpf

# =========================================================
# COMPONENTES
# =========================================================
def botao_copiar(texto: str, rotulo: str, key_unica: str):
    texto_seguro = html.escape(str(texto)).replace("'", "\\'")
    rotulo_seguro = html.escape(rotulo).replace("'", "\\'")
    btn_id = f"btn_{key_unica}"

    components.html(
        f"""
        <div class="copy-btn-wrap">
            <button id="{btn_id}" class="copy-btn" onclick="copiarTexto_{key_unica}()">
                {rotulo_seguro}
            </button>
        </div>

        <script>
            async function copiarTexto_{key_unica}() {{
                const texto = '{texto_seguro}';
                const btn = document.getElementById('{btn_id}');
                const original = btn.innerText;

                try {{
                    await navigator.clipboard.writeText(texto);
                    btn.innerText = 'Copiado!';
                    setTimeout(() => {{
                        btn.innerText = original;
                    }}, 1800);
                }} catch (e) {{
                    alert('Não foi possível copiar automaticamente. Valor: ' + texto);
                }}
            }}
        </script>
        """,
        height=72,
    )

def iniciar_reset_automatico(segundos: int = 40):
    components.html(
        f"""
        <div class="countdown-box">
            Esta consulta será limpa automaticamente em
            <span id="contador">{segundos}</span> segundos.
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
        height=86
    )

# =========================================================
# ESTADO
# =========================================================
if "cpf_input" not in st.session_state:
    st.session_state.cpf_input = ""

# =========================================================
# CABEÇALHO
# =========================================================
st.markdown('<div class="main-title">Consulta de Chave de Ativação</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Digite seu CPF para visualizar sua matrícula e sua chave do Ahgora.</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="steps-box">
    <div style="font-weight:800; margin-bottom:8px;">Como usar</div>
    <div>1. Digite seu CPF</div>
    <div>2. Confira seus dados</div>
    <div>3. Copie sua matrícula e sua chave</div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# CARREGAR BASE
# =========================================================
try:
    df, indice_cpf = carregar_base()
except Exception as e:
    st.error(f"Erro ao carregar a base: {e}")
    st.stop()

# =========================================================
# ENTRADA DO CPF
# =========================================================
cpf_bruto = st.text_input(
    "CPF",
    value=st.session_state.cpf_input,
    placeholder="Digite seu CPF",
    help="Pode digitar com ou sem pontos e traço."
)

cpf_limpo = somente_digitos(cpf_bruto)[:11]

# Máscara visual automática
cpf_mascarado = formatar_cpf(cpf_limpo) if len(cpf_limpo) == 11 else cpf_limpo

if cpf_bruto != cpf_mascarado:
    st.session_state.cpf_input = cpf_mascarado
else:
    st.session_state.cpf_input = cpf_bruto

cpf_consulta = cpf_limpo.zfill(11)[-11:] if cpf_limpo else ""

# =========================================================
# REGRAS DE VALIDAÇÃO / CONSULTA
# =========================================================
if cpf_bruto:
    if len(cpf_limpo) < 11:
        st.warning("Digite os 11 números do CPF para consultar.")
        st.stop()

    if len(cpf_limpo) > 11:
        st.error("CPF inválido.")
        st.stop()

    registro = indice_cpf.get(cpf_consulta)

    if not registro:
        st.error("CPF não encontrado.")
        st.stop()

    st.success("Dados localizados com sucesso.")

    st.markdown(f"""
    <div class="card-box">
        <div class="label-text">Nome</div>
        <div class="value-text">{html.escape(registro["NOME"])}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card-box">
        <div class="label-text">CPF</div>
        <div class="value-text">{html.escape(registro["CPF_FORMATADO"])}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card-box">
        <div class="label-text">Matrícula</div>
        <div class="value-text">{html.escape(registro["MATRICULA"])}</div>
    </div>
    """, unsafe_allow_html=True)
    botao_copiar(registro["MATRICULA"], "Copiar matrícula", "matricula")

    st.markdown(f"""
    <div class="card-box">
        <div class="label-text">Chave de ativação</div>
        <div class="value-text">{html.escape(registro["CHAVE"])}</div>
    </div>
    """, unsafe_allow_html=True)
    botao_copiar(registro["CHAVE"], "Copiar chave", "chave")

    iniciar_reset_automatico(40)

st.markdown(
    '<div class="footer-note">Após 40 segundos, a tela será limpa automaticamente.</div>',
    unsafe_allow_html=True
)