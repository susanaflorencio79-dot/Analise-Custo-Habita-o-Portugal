import streamlit as st
import pandas as pd
import numpy as np

# Configuração da Página
st.set_page_config(page_title="Simulador Crédito Habitação PT", page_icon="🏠", layout="wide")

# --- FUNÇÕES DE CÁLCULO ---
def calcular_prestacao(montante, taxa_anual, anos):
    if taxa_anual == 0:
        return montante / (anos * 12)
    taxa_mensal = (taxa_anual / 100) / 12
    meses = anos * 12
    prestacao = montante * (taxa_mensal * (1 + taxa_mensal)**meses) / ((1 + taxa_mensal)**meses - 1)
    return prestacao

def calcular_montante_maximo(prestacao_mensal, taxa_anual, anos):
    if prestacao_mensal <= 0:
        return 0
    if taxa_anual == 0:
        return prestacao_mensal * anos * 12
    taxa_mensal = (taxa_anual / 100) / 12
    meses = anos * 12
    montante = prestacao_mensal * (1 - (1 + taxa_mensal)**-meses) / taxa_mensal
    return montante

def calcular_limite_anos_bdp(idade):
    if idade <= 30: return 40
    elif 30 < idade <= 35: return 37
    else: return 35

def estimar_imt_is(valor_imovel, finalidade, isencao_jovem=False):
    imposto_selo = valor_imovel * 0.008
    imt = 0
    
    if finalidade == "Habitação Própria Permanente (1ª Habitação)":
        if isencao_jovem and valor_imovel <= 316272:
            return 0, 0
        
        if valor_imovel <= 101917: imt = 0
        elif valor_imovel <= 139412: imt = valor_imovel * 0.02 - 2038.34
        elif valor_imovel <= 190086: imt = valor_imovel * 0.05 - 6220.70
        elif valor_imovel <= 316272: imt = valor_imovel * 0.07 - 10022.42
        elif valor_imovel <= 633453: imt = valor_imovel * 0.08 - 13185.14
        else: imt = valor_imovel * 0.075 
    
    else: # Habitação Secundária ou Arrendamento
        if valor_imovel <= 101917: imt = valor_imovel * 0.01
        elif valor_imovel <= 139412: imt = valor_imovel * 0.02 - 1019.17
        elif valor_imovel <= 190086: imt = valor_imovel * 0.05 - 5201.53
        elif valor_imovel <= 316272: imt = valor_imovel * 0.07 - 9003.25
        elif valor_imovel <= 633453: imt = valor_imovel * 0.08 - 12165.97
        else: imt = valor_imovel * 0.075

    return max(0, imt), imposto_selo


# --- INTERFACE DA APP ---
st.title("🏠 Assistente Inteligente de Crédito Habitação")
st.markdown("Descubra o custo real de comprar casa ou calcule o seu limite de compra com base na taxa de esforço.")

# --- PASSO 1: PERFIL ---
st.header("1. Perfil dos Compradores e Finalidade")
finalidade = st.selectbox("Qual a finalidade do imóvel?", 
                          ["Habitação Própria Permanente (1ª Habitação)", "Habitação Secundária (Férias/Arrendamento)"])

col1, col2 = st.columns(2)
with col1:
    tipo_simulacao = st.radio("Como vai comprar a casa?", ["Sozinho(a)", "Com Parceiro(a)"])
    idade_1 = st.number_input("A sua idade", min_value=18, max_value=70, value=30)
    salario_1 = st.number_input("Seu salário líquido mensal (€)", min_value=500, value=1500, step=100)
    outros_creditos_1 = st.number_input("Prestações de outros créditos seus (€/mês)", min_value=0, value=0, step=50)

if tipo_simulacao == "Com Parceiro(a)":
    with col2:
        st.write("---")
        idade_2 = st.number_input("Idade do parceiro(a)", min_value=18, max_value=70, value=30)
        salario_2 = st.number_input("Salário líquido parceiro(a) (€)", min_value=500, value=1500, step=100)
        outros_creditos_2 = st.number_input("Outros créditos parceiro(a) (€/mês)", min_value=0, value=0, step=50)
    
    idade_mais_velha = max(idade_1, idade_2)
    rendimento_total = salario_1 + salario_2
    creditos_totais = outros_creditos_1 + outros_creditos_2
    jovens_elegiveis = idade_1 <= 35 and idade_2 <= 35
else:
    idade_mais_velha = idade_1
    rendimento_total = salario_1
    creditos_totais = outros_creditos_1
    jovens_elegiveis = idade_1 <= 35

prazo_max_legal = calcular_limite_anos_bdp(idade_mais_velha)

# Definir percentagem máxima de financiamento (90% para 1ª habitação, 80% para secundária)
percentagem_financiamento_max = 0.90 if finalidade == "Habitação Própria Permanente (1ª Habitação)" else 0.80
percentagem_entrada_min = 1 - percentagem_financiamento_max

# --- PASSO 2: CONDIÇÕES DO BANCO ---
st.header("2. Prazos e Taxas do Banco")
col3, col4 = st.columns(2)

with col3:
    prazo_desejado = st.slider("Prazo do Empréstimo (Anos)", min_value=10, max_value=40, value=min(30, prazo_max_legal))
    if prazo_desejado > prazo_max_legal:
        st.error(f"⚠️ Para a idade de {idade_mais_velha} anos, o prazo máximo é de **{prazo_max_legal} anos**.")
        prazo_utilizado = prazo_max_legal
    else:
        prazo_utilizado = prazo_desejado
    
    if finalidade == "Habitação Própria Permanente (1ª Habitação)":
        isencao_imt = st.checkbox("Aplicar Isenção IMT Jovem (Até 35 anos)", value=jovens_elegiveis)
    else:
        st.info("ℹ️ A isenção de IMT Jovem não é aplicável a habitações secundárias.")
        isencao_imt = False

with col4:
    tipo_taxa = st.radio("Tipo de Taxa", ["Variável (Indexada à Euribor)", "Fixa"])
    if "Variável" in tipo_taxa:
        euribor = st.number_input("Euribor Atual (%)", value=3.5, step=0.1)
        spread = st.number_input("Spread do Banco (%)", value=0.8, step=0.1)
        taxa_final = euribor + spread
    else:
        taxa_final = st.number_input("Taxa Fixa Oferecida (%)", value=4.0, step=0.1)


# --- PASSO 3: O GRANDE DILEMA ---
st.header("3. O que pretende simular?")
modo_calculo = st.radio(
    "Escolha o seu ponto de partida:", 
    ["Saber o custo de um imóvel específico (Inserir Valor do Imóvel)", 
     "Saber até quanto posso comprar (Inserir Taxa de Esforço Desejada)"]
)

st.write("---")

if "custo de um imóvel específico" in modo_calculo:
    valor_imovel = st.number_input("Valor de compra do imóvel (€)", min_value=50000, value=200000, step=5000)
    entrada_minima = valor_imovel * percentagem_entrada_min
    
    st.info(f"Para {finalidade}, a entrada mínima exigida por lei é de **{percentagem_entrada_min*100:.0f}%**.")
    entrada = st.number_input(f"A sua Entrada Inicial (Mínimo: {entrada_minima:,.0f}€)", 
                              min_value=0.0, value=float(entrada_minima), step=1000.0)
    
    montante_financiado = valor_imovel - entrada
    prestacao_mensal = calcular_prestacao(montante_financiado, taxa_final, prazo_utilizado)
    taxa_esforco = ((prestacao_mensal + creditos_totais) / rendimento_total) * 100

else:
    taxa_esforco_alvo = st.slider("Qual a Taxa de Esforço máxima que deseja atingir? (%)", min_value=10, max_value=50, value=30)
    prestacao_mensal = ((taxa_esforco_alvo / 100) * rendimento_total) - creditos_totais
    
    if prestacao_mensal <= 0:
        st.error("🚨 Os seus créditos atuais já ultrapassam esta taxa de esforço. Não tem margem para financiamento.")
        montante_financiado = 0
        valor_imovel = 0
        entrada = 0
    else:
        montante_financiado = calcular_montante_maximo(prestacao_mensal, taxa_final, prazo_utilizado)
        # Assumindo financiamento máximo legal (90% ou 80%)
        valor_imovel = montante_financiado / percentagem_financiamento_max
        entrada = valor_imovel * percentagem_entrada_min
        taxa_esforco = taxa_esforco_alvo

# --- PASSO 4: RESULTADOS ---
if montante_financiado > 0:
    st.header("4. Resultados da Simulação")
    
    if "até quanto posso comprar" in modo_calculo:
        st.success(f"Para manter uma taxa de esforço de **{taxa_esforco:.1f}%**, o valor máximo da casa é **€ {valor_imovel:,.2f}** (assumindo {percentagem_entrada_min*100:.0f}% de entrada).")
    
    imt, imposto_selo = estimar_imt_is(valor_imovel, finalidade, isencao_imt)
    capital_necessario_inicio = entrada + imt + imposto_selo
    ltv = (montante_financiado / valor_imovel) * 100

    res1, res2, res3 = st.columns(3)
    res1.metric("Prestação Mensal", f"€ {prestacao_mensal:,.2f}")
    res2.metric("Montante Financiado", f"€ {montante_financiado:,.2f}", f"LTV: {ltv:.1f}%")
    res3.metric("Capital Inicial Necessário", f"€ {capital_necessario_inicio:,.2f}", "Entrada + Impostos")

    st.subheader("Análise de Esforço")
    st.progress(min(taxa_esforco / 100, 1.0))
    if taxa_esforco <= 33:
        st.write("🟢 **Taxa Saudável:** Excelente margem de segurança.")
    elif 33 < taxa_esforco <= 40:
        st.write("🟡 **Taxa Elevada:** Requer cuidado; aprovação sujeita a maior escrutínio bancário.")
    else:
        st.write("🔴 **Risco Máximo:** Muito dificilmente será aprovado pelos bancos tradicionais.")

    with st.expander("Ver detalhe dos Custos Iniciais (Impostos e Entrada)"):
        st.write(f"- **Valor do Imóvel Base:** € {valor_imovel:,.2f}")
        st.write(f"- **Entrada Inicial ({percentagem_entrada_min*100:.0f}%):** € {entrada:,.2f}")
        st.write(f"- **IMT Estimado:** € {imt:,.2f}")
        st.write(f"- **Imposto de Selo (Imóvel):** € {imposto_selo:,.2f}")
        st.info("Nota: Faltam os custos de processo e escritura (aprox. 1,500€ - 2,500€).")