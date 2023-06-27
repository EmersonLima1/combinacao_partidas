import random
import requests
import pandas as pd
import streamlit as st
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="InPES Futebol Virtual", page_icon=":soccer:")

st.title('**Resultados do Futebol Virtual**')
st.write('\n\n')

# Perguntas para o usuário
resultado_partida_desejado = st.selectbox("Qual resultado deseja encontrar?", ['Casa', 'Empate', 'Fora', 'Under 0.5', 'Under 1.5', 'Under 2.5', 'Under 3.5', 'Over 0.5', 'Over 1.5', 'Over 2.5', 'Over 3.5', '5+', 'Ambas marcaram', 'Ambas não marcaram'])
num_combinacoes = st.number_input("Qual o número de combinações de partidas?", min_value=3, max_value = 10, value=3, step=1)
num_resultados = st.number_input("Quantos resultados de partidas deseja exibir?", min_value=5, max_value = 25, value=5, step=1)

def gerar_resultados():

  sheet_id = '1-OpwOkZbencR-EGbQiTkgDWKzEY8Y-t0B7TlmRuUlaY'
  url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'

  response = requests.get(url)
  data = response.content

  excel_data = pd.ExcelFile(BytesIO(data), engine='openpyxl')
  sheet_names = excel_data.sheet_names

  # Criação das combinações
  classes = ['Casa', 'Empate', 'Fora', 'Under 0.5', 'Under 1.5', 'Under 2.5', 'Under 3.5', 'Over 0.5', 'Over 1.5', 'Over 2.5', 'Over 3.5', '5+', 'Ambas marcaram', 'Ambas não marcaram']

  # Gerar todas as combinações possíveis dos 14 valores da lista 'classes', levando em consideração que a ordem não importa e os valores podem ser repetidos
  combinacoes = list(combinations_with_replacement(classes, num_combinacoes))

  for sheet_name in sheet_names:
      
      # Tratando o arquivo Excel e obtendo o DataFrame tratado
      df = excel_data.parse(sheet_name)

      # Define a primeira linha como os nomes das colunas
      df.columns = df.iloc[0]

      # Remove a primeira linha, que agora são os nomes das colunas duplicados
      df = df[1:].reset_index(drop=True)

      # Obtém todas as colunas, exceto as duas últimas
      colunas_para_manter = df.columns[:-3]

      # Mantém apenas as colunas selecionadas
      df = df[colunas_para_manter]

      # Inverte o dataframe
      df = df.sort_index(ascending=False)

      # Reseta o index
      df = df.reset_index(drop=True)

      # Função para extrair os resultados do primeiro tempo, tempo final e partidas
      def extrair_resultados(resultado):
          if resultado != '?\n\n?':
              resultado_split = resultado.split('\n\n')
              primeiro_tempo = resultado_split[1]
              tempo_final = resultado_split[0]
              return primeiro_tempo, tempo_final
          else:
              return None, None

      # Criando listas vazias para armazenar os valores extraídos
      primeiro_tempo_list = []
      tempo_final_list = []
      partidas_list = []

      # Percorrendo o dataframe original e extraindo os resultados
      for index, row in df.iterrows():
          for col in df.columns[1:]:
              resultado = row[col]
              primeiro_tempo, tempo_final = extrair_resultados(resultado)
              primeiro_tempo_list.append(primeiro_tempo)
              tempo_final_list.append(tempo_final)
              partidas_list.append(col)

      # Criando o novo dataframe com as colunas desejadas
      df_novo = pd.DataFrame({
          'Primeiro tempo': primeiro_tempo_list,
          'Tempo final': tempo_final_list,
      })


      num_linhas = len(df_novo)
      df_novo['Partidas'] = range(1, num_linhas + 1)

      # Obtendo o nome da última coluna
      ultima_coluna = df_novo.columns[-1]

      # Extraindo a coluna "Partidas"
      coluna_partidas = df_novo.pop(ultima_coluna)

      # Inserindo a coluna "Partidas" na terceira posição
      df_novo.insert(0, ultima_coluna, coluna_partidas)

      df_novo = df_novo.dropna(subset=['Primeiro tempo', 'Tempo final'])

      df_novo = df_novo[~df_novo['Primeiro tempo'].str.contains('\.', na=False) & ~df_novo['Tempo final'].str.contains('\.', na=False)]

      df_novo['Primeiro tempo'] = df_novo['Primeiro tempo'].replace('oth', '9x9')

      # Remover células com valor "?"
      df_novo = df_novo[(df_novo['Primeiro tempo'] != '?') & (df_novo['Tempo final'] != '?')]

      df = df_novo

      # Lista para armazenar as informações transformadas
      resultados_partida_transformados = []

      # Percorrer as linhas do dataframe original
      for index, row in df.iterrows():
          tempo_final = row['Tempo final']
          
          # Dividir o valor no formato '0x0' em gols_casa e gols_visitante
          gols_casa, gols_visitante = tempo_final.split('x')
          gols_casa = int(gols_casa)
          gols_visitante = int(gols_visitante)

          # Determinar a descrição do resultado com base nos gols marcados por ambas as equipes
          descricao_resultado = "Ambas marcaram" if gols_casa > 0 and gols_visitante > 0 else "Ambas não marcaram"

          # Determinar o resultado da partida com base nos gols marcados por cada equipe
          resultado_partida = 'Casa' if gols_casa > gols_visitante else 'Fora' if gols_visitante > gols_casa else 'Empate'

          # Calcular a soma dos gols marcados
          soma_gols = gols_casa + gols_visitante

          # Determinar a faixa de gols com base na soma dos gols marcados
          if soma_gols >= 5:
              faixa_gols = "Over 0.5 / Over 1.5 / Over 2.5 / Over 3.5 / 5+"
          elif soma_gols == 4:
              faixa_gols = "Over 0.5 / Over 1.5 / Over 2.5 / Over 3.5"
          elif soma_gols == 3:
              faixa_gols = "Over 0.5 / Over 1.5 / Over 2.5 / Under 3.5"
          elif soma_gols == 2:
              faixa_gols = "Over 0.5 / Over 1.5 / Under 2.5 / Under 3.5"
          elif soma_gols == 1:
              faixa_gols = "Over 0.5 / Under 1.5 / Under 2.5 / Under 3.5"
          else:
              faixa_gols = "Under 0.5 / Under 1.5 / Under 2.5 / Under 3.5"

          # Concatenar as informações do resultado em uma string e adicionar à lista de resultados transformados
          resultados_partida_transformados.append(f"{descricao_resultado} - {resultado_partida} - {faixa_gols}")

      # Criar o novo dataframe com as colunas 'Partidas' e 'Classes'
      novo_df = pd.DataFrame({'Partidas': df['Partidas'], 'Classes': resultados_partida_transformados})

      # Lista de combinações
      combinações = combinacoes

      # Dicionário para armazenar o contador e as partidas de Ambas marcaram de cada combinação
      contador_combinações = {}

      # Percorrer a lista de combinações
      for combinação in combinações:
          contador = 0
          partidas_ambas_marcaram = []
          total_ocorrências = 0

          # Percorrer as linhas do dataframe
          for index, row in novo_df.iterrows():
              ocorre_combinação = True
              # Verificar se a combinação ocorre nas cinco partidas consecutivas
              for i, resultado in enumerate(combinação):
                  if index + i < len(novo_df):
                      if resultado not in novo_df.iloc[index+i]['Classes']:
                          ocorre_combinação = False
                          break
                  else:
                      ocorre_combinação = False
                      break
              
              if ocorre_combinação and index + 5 < len(novo_df):
                  partida_ambas_marcaram = novo_df.iloc[index+5]['Classes']
                  if resultado_partida_desejado in partida_ambas_marcaram:
                      contador += 1
                      partidas_ambas_marcaram.append(index+6)
                  total_ocorrências += 1

          # Calcular a acurácia da combinação
          if total_ocorrências > 0:
              acurácia = contador / total_ocorrências
          else:
              acurácia = 0

          # Armazenar o contador, acurácia e partidas de Ambas marcaram da combinação no dicionário
          contador_combinações[combinação] = {'contador': contador, 'acurácia': acurácia, 'partidas_ambas_marcaram': partidas_ambas_marcaram}

      # Criar dataframe com os resultados
      resultado_df = pd.DataFrame.from_dict(contador_combinações, orient='index', columns=['contador', 'acurácia', 'partidas_ambas_marcaram'])
      resultado_df = resultado_df.reset_index().rename(columns={'index': 'Combinação'})

      # Ordenar pelo valor de acurácia em ordem decrescente e contador em ordem decrescente
      resultado_df = resultado_df.sort_values(['acurácia', 'contador'], ascending=[False, False])

      st.write('Melhores combinações da '+ sheet_name + '\n')

      # Imprimir as 10 combinações mais assertivas com suas respectivas acurácias e partidas de Ambas marcaram
      top_combinações = resultado_df.head(num_resultados)
          
      st.write(top_combinações)

      # Verifica se o botão "Exportar resultados" foi pressionado
      if st.button("Exportar resultados"):

        # Cria um arquivo Excel com páginas correspondentes a cada sheet_name
        with pd.ExcelWriter('resultados.xlsx') as writer:
            for sheet_name, combinações_sheet in resultado_df.groupby('sheet_name'):
                combinações_sheet.to_excel(writer, sheet_name=sheet_name, index=False)
 
# Botão "Gerar resultados"
if st.button("Gerar resultados"):
    gerar_resultados()
