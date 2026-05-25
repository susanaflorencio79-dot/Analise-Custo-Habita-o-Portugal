import streamlit as st
import plotly.graph_objects as go

# 1. Configuração da Página Web
st.set_page_config(page_title="Investigação Habitação", page_icon="🏠", layout="wide")

st.title("Investigação de Dados: O Custo Real da Habitação")
st.markdown("Plataforma independente de análise do impacto do mercado imobiliário nos rendimentos reais em Portugal.")

# Função para estimar o Salário Líquido aproximado (Trabalhador Dependente, Solteiro, Sem Filhos)
def calcular_salario_liquido(bruto):
    if bruto <= 820:
        irs = 0.0
    elif bruto <= 1100:
        irs = 0.08
    elif bruto <= 1500:
        irs = 0.12
    elif bruto <= 2000:
        irs = 0.16
    elif bruto <= 3000:
        irs = 0.22
    elif bruto <= 5000:
        irs = 0.26
    else:
        irs = 0.30
    
    seg_social = 0.11
    liquido = bruto * (1 - (seg_social + irs))
    return max(liquido, 0.0)

# 2. Painel Lateral com Input de Elevada Precisão
with st.sidebar:
    st.header("Parâmetros")
    
    preco_m2 = st.number_input("Preço por m² (€)", min_value=100.0, max_value=25000.0, value=2400.0, step=10.0)
    salario_bruto = st.number_input("O Teu Salário Mensal Bruto (€)", min_value=500.0, max_value=20000.0, value=1200.0, step=10.0)
    area = st.number_input("Área Total da Habitação (m²)", min_value=10.0, max_value=600.0, value=80.0, step=1.0)
    taxa_juro = st.number_input("Taxa de Juro / TAEG (%)", min_value=0.0, max_value=15.0, value=4.0, step=0.05)
    anos = st.number_input("Prazo do Empréstimo (Anos)", min_value=5, max_value=50, value=35, step=1)

# Cálculos de Base
salario_liquido = calcular_salario_liquido(salario_bruto)
total_casa = preco_m2 * area
v_emp = total_casa * 0.90
r_mensal = (taxa_juro / 100) / 12
n_meses = anos * 12

if taxa_juro > 0:
    prestacao = v_emp * (r_mensal * (1 + r_mensal)**n_meses) / ((1 + r_mensal)**n_meses - 1)
else:
    prestacao = v_emp / n_meses

# Rácios Brutos vs Líquidos
meses_1m2_bruto = preco_m2 / salario_bruto
meses_1m2_liquido = preco_m2 / salario_liquido

t_esforco_bruto = (prestacao / salario_bruto) * 100
t_esforco_liquido = (prestacao / salario_liquido) * 100

# Constantes Oficiais do Baseline para o Separador 2
SALARIO_MINIMO_BRUTO = 820.0
SALARIO_MINIMO_LIQUIDO = calcular_salario_liquido(SALARIO_MINIMO_BRUTO)
SALARIO_MEDIO_BRUTO = 1600.0
SALARIO_MEDIO_LIQUIDO = calcular_salario_liquido(SALARIO_MEDIO_BRUTO)

# 3. Criação de Separadores
tab_pessoal, tab_desigualdade = st.tabs(["Simulador de Esforço Pessoal", "Comparação de Desigualdade"])

# ==========================================
# SEPARADOR 1: SIMULAÇÃO PESSOAL
# ==========================================
with tab_pessoal:
    st.subheader("Análise de Viabilidade Real (Financiamento a 90%)")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Custo Total do Imóvel", f"{total_casa:,.0f} €".replace(',', 'X').replace('.', ',').replace('X', '.'))
    col2.metric("Montante a Financiar", f"{v_emp:,.0f} €".replace(',', 'X').replace('.', ',').replace('X', '.'))
    col3.metric("Salário Bruto Introduzido", f"{salario_bruto:,.0f} €".replace(',', 'X').replace('.', ',').replace('X', '.'))
    col4.metric("Salário Líquido Estimado", f"{salario_liquido:,.0f} €".replace(',', 'X').replace('.', ',').replace('X', '.'))

    # Alerta baseado no Esforço Líquido (A realidade bancária prática)
    if t_esforco_liquido <= 33:
        st.success(f"✅ Prestação Mensal: **{prestacao:,.0f} €** | Taxa de Esforço Líquida: **{t_esforco_liquido:.1f}%** (Cenário Seguro e Sustentável)")
        cor_esforco = '#22c55e'
    elif t_esforco_liquido <= 50:
        st.warning(f"⚠️ Prestação Mensal: **{prestacao:,.0f} €** | Taxa de Esforço Líquida: **{t_esforco_liquido:.1f}%** (Zona de Risco. O orçamento mensal fica apertado)")
        cor_esforco = '#f59e0b'
    else:
        st.error(f"🚨 Prestação Mensal: **{prestacao:,.0f} €** | Taxa de Esforço Líquida: **{t_esforco_liquido:.1f}%** (Zona Crítica. Sobram apenas {(salario_liquido - prestacao):.0f}€ para o resto do mês)")
        cor_esforco = '#ef4444'

    st.markdown("### Comparação de Impacto: Rendimento Bruto vs. Rendimento Líquido")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            name='Esforço Bruto', y=['Esforço Bruto', 'Esforço Líquido'], x=[meses_1m2_bruto, meses_1m2_liquido],
            orientation='h', marker=dict(color=['#3b82f6', '#1d4ed8']),
            text=[f"{meses_1m2_bruto:.1f} meses", f"{meses_1m2_liquido:.1f} meses"], textposition='inside'
        ))
        fig1.update_layout(title="<b>Meses de Trabalho Necessários por 1m²</b>", height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "gray"})
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            y=['Média Bruta', 'Realidade Líquida'], x=[t_esforco_bruto, t_esforco_liquido],
            orientation='h', marker=dict(color=['#cbd5e1', cor_esforco]),
            text=[f"{t_esforco_bruto:.1f}%", f"{t_esforco_liquido:.1f}%"], textposition='inside'
        ))
        fig2.add_shape(type="line", x0=33, y0=-0.5, x1=33, y1=1.5, line=dict(color="white", width=2, dash="dash"))
        fig2.update_layout(title="<b>A Derivação da Taxa de Esforço Real (%)</b>", height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "gray"})
        st.plotly_chart(fig2, use_container_width=True)

# ==========================================
# SEPARADOR 2: AUDITORIA DE DESIGUALDADE MACRO
# ==========================================
with tab_desigualdade:
    st.subheader("Auditoria Líquida: Salário Mínimo vs. Salário Médio Nacional")
    st.markdown("A ilusão estatística cai quando removemos os impostos estatais automática da folha de vencimento.")

    fosso_bruto = (preco_m2 / SALARIO_MINIMO_BRUTO) - (preco_m2 / SALARIO_MEDIO_BRUTO)
    fosso_liquido = meses_1m2_liquido_minimo = (preco_m2 / SALARIO_MINIMO_LIQUIDO) - (preco_m2 / SALARIO_MEDIO_LIQUIDO)

    c1, c2 = st.columns(2)
    c1.metric("Fosso Nominal (Salário Bruto)", f"{fosso_bruto:.1f} meses")
    c2.metric("Fosso Efetivo (Salário Líquido)", f"{fosso_liquido:.1f} meses", delta=f"{fosso_liquido - fosso_bruto:.1f} meses escondidos pelo IRS", delta_color="inverse")

    st.markdown(f"""
    <div style="background-color: rgba(239, 68, 68, 0.05); padding: 15px; border-left: 5px solid #ef4444; border-radius: 4px; margin: 15px 0;">
        <strong style="color: #ef4444;">Evidência de Dados:</strong> No papel (bruto), a diferença de esforço entre as duas classes para pagar 1m² é de <b>{fosso_bruto:.1f} meses</b>. No entanto, após a retenção fiscal real na carteira (líquido), o fosso dispara para <b>{fosso_liquido:.1f} meses de vida ativa</b>. A fiscalidade amplia a assimetria no acesso à habitação.
    </div>
    """, unsafe_allow_html=True)

    # Gráfico Comparativo Macro Líquido
    fig_macro = go.Figure()
    fig_macro.add_trace(go.Bar(
        y=['Salário Médio Líquido', 'Salário Mínimo Líquido'],
        x=[preco_m2 / SALARIO_MEDIO_LIQUIDO, preco_m2 / SALARIO_MINIMO_LIQUIDO],
        orientation='h', marker=dict(color=['#a855f7', '#ec4899']),
        text=[f"{(preco_m2 / SALARIO_MEDIO_LIQUIDO):.1f} meses", f"{(preco_m2 / SALARIO_MINIMO_LIQUIDO):.1f} meses"], textposition='inside'
    ))
    fig_macro.update_layout(title="Esforço por Metro Quadrado em Rendimento Disponível Real", height=250, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={'color': "gray"})
    st.plotly_chart(fig_macro, use_container_width=True)