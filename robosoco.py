import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import OneHotEncoder
import random
import os
from time import sleep
import datetime
import matplotlib.pyplot as plt # Importa o gráfico
import tkinter as tk
from tkinter import ttk

# --- CLASSE QUE DEFINE O CENÁRIO (O TÚNEL) --- 
class Cenario:
    """
    Representa o ambiente do túnel com seus perigos e vítimas.
    """
    def __init__(self, comprimento=500, largura=8):
        tipo_acidente = 'linha_amarela' # Força o cenário a ser sempre este
        print(f"--- Criando Cenário: Túnel de {comprimento}m (Acidente: {tipo_acidente.upper()}) ---")
        self.comprimento = comprimento
        self.largura = largura
        self.tipo_acidente = tipo_acidente
        self.objetos = [] 

        # Simulação do incêndio do ônibus na Linha Amarela
        print("--- ATENÇÃO: Cenário especial 'Linha Amarela' ativado. ---")
        # O ônibus pegando fogo é um grande foco de calor e um escombro
        self.objetos.append({'tipo': 'fogo', 'x': 350, 'y': 4, 'temp': 800, 'raio': 25}) # Fogo intenso e amplo
        self.objetos.append({'tipo': 'escombro', 'x': 350, 'y': 4, 'risco_estrutural': 3, 'raio': 10}) # Risco estrutural do ônibus
        # Vítima crítica perto do fogo
        self.objetos.append({'tipo': 'vitima', 'x': 355, 'y': 5, 'temp': 38.0, 'gravidade': 'critica', 'estado_vital': 'viva', 'consciencia': 'desmaiada', 'condicao': 'respirando', 'raio': 5})
        # Vítima moderada que se afastou
        self.objetos.append({'tipo': 'vitima', 'x': 320, 'y': 2, 'temp': 37.0, 'gravidade': 'moderada', 'estado_vital': 'viva', 'consciencia': 'acordada', 'condicao': 'em crise', 'raio': 4})
        # --- NOVAS VÍTIMAS ADICIONADAS ---
        # Vítima com sangramento (Prioridade Máxima)
        self.objetos.append({'tipo': 'vitima', 'x': 150, 'y': 3, 'temp': 37.5, 'gravidade': 'grave', 'estado_vital': 'viva', 'consciencia': 'desmaiada', 'condicao': 'sangramento', 'raio': 3})
        # Vítima com ferimentos leves (Prioridade Baixa - será ignorada pela IA)
        self.objetos.append({'tipo': 'vitima', 'x': 450, 'y': 6, 'temp': 36.8, 'gravidade': 'leve', 'estado_vital': 'viva', 'consciencia': 'acordada', 'condicao': 'normal', 'raio': 3})

    def ler_sensores_na_posicao(self, x, y):
        """ Simula a leitura dos sensores do robô em uma dada coordenada (x, y). """
        dados = {'temp': 25.0, 'co2': 415, 'risco_estrutural': 0, 'vitima_detectada': None}

        for obj in self.objetos:
            dist = ((x - obj['x'])**2 + (y - obj['y'])**2)**0.5
            
            if 'temp' in obj and dist < obj.get('raio', 10):
                temp_adicional = (obj['temp'] - dados['temp']) * (1 - dist / obj.get('raio', 10))
                dados['temp'] = max(dados['temp'], dados['temp'] + temp_adicional)

            # Detecção de Vítima (Níveis de Gravidade)
            if obj['tipo'] == 'vitima' and dist < obj.get('raio', 2): # Agora usa o raio configurável do objeto
                dados['vitima_detectada'] = {
                    'pos': (obj['x'], obj['y']), 
                    'gravidade': obj['gravidade'],
                    'estado_vital': obj.get('estado_vital', 'desconhecido'),
                    'consciencia': obj.get('consciencia', 'desconhecido'),
                    'condicao': obj.get('condicao', 'desconhecido')
                }

            if 'risco_estrutural' in obj and dist < obj.get('raio', 10):
                dados['risco_estrutural'] = max(dados['risco_estrutural'], obj['risco_estrutural'])

        dados['temp'] = round(dados['temp'] + random.uniform(-0.5, 0.5), 1)
        dados['co2'] += random.randint(-10, 10)
        return dados

# --- CLASSE QUE REPRESENTA O ROBÔ ---
class Robo:
    """
    Representa o robô, seus sensores, estado e comunicação.
    """
    def __init__(self, central_controle):
        self.pos_x = 0
        self.pos_y = 4 
        self.bateria = 100.0
        self.status = "Explorando"
        self.central_controle = central_controle 
        self.memoria_fotos = {}
        self.kits_primeiros_socorros = 3 # Robô começa com 3 kits

    def mover(self, cenario):
        """ Move o robô para frente, se o status permitir. """
        if self.status != "Explorando":
            return

        if self.pos_x < cenario.comprimento:
            self.pos_x += 1 # Avança 1 metro
            self.bateria -= 0.1 
        else:
            self.status = "Fim do Túnel"
            print("[Robô] Cheguei ao fim do túnel.")

    def executar_passo_missao(self, cenario):
        """ Um ciclo completo de operação do robô. """
        # --- NOVA LÓGICA DE BATERIA ---
        if self.bateria < 20 and self.status != "Retornando":
            print("[Robô] 🔋 Bateria baixa (< 20%). Iniciando retorno à base.")
            self.status = "Retornando"
            # Não para a missão, apenas muda o status. A central vai lidar com isso.

        if self.status == "Retornando":
            self.pos_x -= 1 # Move para trás
            self.bateria -= 0.1
            if self.pos_x <= 0:
                self.status = "Bateria Esgotada" # Sinaliza o fim da missão na base

        # 1. Mover (se estiver explorando)
        self.mover(cenario)
        
        # 2. Ler Sensores na nova posição
        dados_sensores = cenario.ler_sensores_na_posicao(self.pos_x, self.pos_y)
        
        # 3. Montar o pacote de dados para a central
        pacote_dados = {
            'timestamp': datetime.datetime.now().isoformat(),
            'pos_x': self.pos_x,
            'pos_y': self.pos_y, 
            'bateria': round(self.bateria, 1),
            'status_robo': self.status,
            'sensores': dados_sensores
        }

        # 4. Envia dados para a central (que vai tomar a decisão)
        comando_recebido = self.central_controle.receber_dados_robo(pacote_dados)
        
        # 5. Processa o comando recebido
        self.processar_comando(comando_recebido, pacote_dados)
        
        if self.status == "Bateria Esgotada":
            return False # Encerra o loop da missão
            
        return True # Continua a missão

    def processar_comando(self, comando, dados_atuais):
        """ Executa um comando AUTOMÁTICO recebido da Central. """
        if not comando:
            return

        if comando['acao'] == 'REGISTRAR_FOTO_TERMICA':
            self.status = "Registrando Foto"
            foto_id = f"foto_termica_{self.pos_x}m"
            conteudo_foto = {
                "pos_x": self.pos_x,
                "temp_max_registrada": dados_atuais['sensores']['temp'],
                "dados_vitima": dados_atuais['sensores']['vitima_detectada']
            }
            self.memoria_fotos[foto_id] = conteudo_foto
            print(f"[Robô] 📸 Foto térmica '{foto_id}' registrada com sucesso!")
            self.central_controle.confirmar_registro_foto(foto_id, conteudo_foto)
            self.status = "Aguardando" # Avisa a central que terminou a ação
        
        elif comando['acao'] == 'CONTINUAR_EXPLORACAO':
            self.status = "Explorando"
        
        elif comando['acao'] == 'RETORNAR_BASE':
            self.status = "Retornando"
            print("[Robô] Rota de retorno iniciada.")
        
        elif comando['acao'] == 'MANTER_POSICAO':
            self.status = "Aguardando"

        elif comando['acao'] == 'SOLTAR_KIT_PRIMEIROS_SOCORROS':
            self.status = "Ação Imediata"
            if self.kits_primeiros_socorros > 0:
                self.kits_primeiros_socorros -= 1
                print(f"[Robô] 🩹 Kit de primeiros socorros liberado na posição {self.pos_x}m. Kits restantes: {self.kits_primeiros_socorros}.")
            else:
                print(f"[Robô] ⚠️ Tentativa de liberar kit, mas não há mais kits disponíveis.")
            self.status = "Aguardando" # Avisa a central que terminou a ação

# --- CLASSE DA CENTRAL DE CONTROLE (AUTOMÁTICA) ---
class CentralDeControle:
    """
    Simula a interface do operador (TERMINAL) e a tela de rastreio (GRÁFICO)
    AGORA EM MODO 100% AUTOMÁTICO.
    """
    def __init__(self):
        self.log_missao = []
        self.alertas = []
        
        # --- NOVOS Atributos da Central Automática ---
        self.vitimas_registradas = set() # A "MEMÓRIA" das vítimas já vistas
        self.estado_automatico = {}      # Gerencia a "sequência" de ações
        self.missao_ativa = True         # Flag para controlar o loop principal

        # --- NOVOS Atributos para o Modelo de IA ---
        self.modelo_prioridade = None
        self.encoder_ia = None
        self._treinar_modelo_prioridade() # Treina o modelo na inicialização
        
        # --- Variáveis para o GRÁFICO ---
        self.fig, self.ax = None, None
        self.mapa_x, self.mapa_y = [], [] 
        self.mapa_vitimas_x, self.mapa_vitimas_y = [], [] 

        # --- NOVOS Atributos para a Tabela de Log (Tkinter) ---
        self.root_log = None
        self.tree_log = None

    def _treinar_modelo_prioridade(self):
        """Cria e treina um modelo de IA simples para classificar a prioridade das vítimas."""
        print("[Central IA] Treinando modelo de priorização de vítimas...")

        # Dados de treinamento sintéticos
        # Features: [gravidade, consciencia, condicao]
        # Target: prioridade (1: Alta, 2: Média, 3: Baixa)
        dados_treino = [
            ['critica', 'desmaiada', 'sangramento', 1],
            ['grave', 'desmaiada', 'sangramento', 1],
            ['grave', 'desmaiada', 'respirando', 1],
            ['moderada', 'acordada', 'em crise', 2],
            ['moderada', 'desmaiada', 'respirando', 2],
            ['moderada', 'acordada', 'normal', 2],
            ['leve', 'acordada', 'em crise', 2],
            ['leve', 'acordada', 'normal', 3],
        ]
        df_treino = pd.DataFrame(dados_treino, columns=['gravidade', 'consciencia', 'condicao', 'prioridade'])

        # Prepara os dados para o modelo (One-Hot Encoding)
        X_cat = df_treino[['gravidade', 'consciencia', 'condicao']]
        y = df_treino['prioridade']

        self.encoder_ia = OneHotEncoder(handle_unknown='ignore')
        X_encoded = self.encoder_ia.fit_transform(X_cat)

        # Cria e treina o modelo (Árvore de Decisão)
        self.modelo_prioridade = DecisionTreeClassifier(random_state=42)
        self.modelo_prioridade.fit(X_encoded, y)
        print("[Central IA] Modelo treinado com sucesso!")

    def _prever_prioridade_vitima(self, vitima):
        """Usa o modelo de IA para prever a prioridade de uma vítima."""
        dados_vitima = pd.DataFrame([[vitima['gravidade'], vitima['consciencia'], vitima['condicao']]], columns=['gravidade', 'consciencia', 'condicao'])
        dados_encoded = self.encoder_ia.transform(dados_vitima)
        return self.modelo_prioridade.predict(dados_encoded)[0]

    def _configurar_grafico(self, cenario):
        """(Etapa 1) Cria a Janela do Gráfico"""
        print("[Central] Abrindo janela do mapa da missão...")
        plt.ion() 
        plt.close(1) # Força o fechamento da "Figura 1" fantasma, se existir
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.ax.set_xlim(0, cenario.comprimento)
        self.ax.set_ylim(0, cenario.largura + 2) 
        
    def _atualizar_grafico(self, pacote_dados, alerta_vitima=False):
        """(Etapa 2) Atualiza o Gráfico em Tempo Real"""
        x_atual = pacote_dados['pos_x']
        y_atual = pacote_dados['pos_y']
        bateria = pacote_dados['bateria']
        status = pacote_dados['status_robo']

        self.mapa_x.append(x_atual)
        self.mapa_y.append(y_atual)
        if alerta_vitima:
            self.mapa_vitimas_x.append(x_atual)
            self.mapa_vitimas_y.append(y_atual)

        self.ax.clear() 
        
        self.ax.plot(self.mapa_x, self.mapa_y, '.-', color='gray', alpha=0.5, label='Caminho Percorrido')
        self.ax.plot(x_atual, y_atual, 'o', color='blue', markersize=10, label=f'Posição Atual Robô ({status})')
        if self.mapa_vitimas_x:
            self.ax.plot(self.mapa_vitimas_x, self.mapa_vitimas_y, 'X', color='red', markersize=15, label='Vítima Detectada')

        self.ax.set_title(f"MAPA DA MISSÃO: TÚNEL (Ponto {x_atual}m) | Bateria: {bateria:.0f}%")
        self.ax.legend(loc='upper left')
        self.ax.set_xlim(0, 500) 
        self.ax.set_ylim(0, 10)  
        
        plt.pause(0.001) 

    def _configurar_tabela_log(self):
        """(Etapa 1.B) Cria a janela e a tabela para o log de comunicação."""
        print("[Central] Abrindo janela de log de comunicação...")
        self.root_log = tk.Tk()
        self.root_log.title("Log de Comunicação - Central RoboSoco")
        self.root_log.geometry("900x400")

        # Cria o frame e a scrollbar
        frame = ttk.Frame(self.root_log)
        frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)

        # Cria a tabela (TreeView)
        self.tree_log = ttk.Treeview(frame, columns=("Timestamp", "Fonte", "Mensagem", "Ação IA"), show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree_log.yview)

        # Define os cabeçalhos
        self.tree_log.heading("Timestamp", text="Timestamp")
        self.tree_log.heading("Fonte", text="Fonte")
        self.tree_log.heading("Mensagem", text="Mensagem Recebida / Status")
        self.tree_log.heading("Ação IA", text="Comando Enviado pela IA")

        # Ajusta as colunas
        self.tree_log.column("Timestamp", width=160, anchor='w')
        self.tree_log.column("Fonte", width=80, anchor='center')
        self.tree_log.column("Mensagem", width=400, anchor='w')
        self.tree_log.column("Ação IA", width=200, anchor='w')

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_log.pack(fill=tk.BOTH, expand=True)

        # Adiciona um manipulador para o evento de fechar a janela
        self.root_log.protocol("WM_DELETE_WINDOW", self._on_closing_log_window)

    def iniciar_missao(self, robo, cenario):
        """Inicia a missão, ligando o GRÁFICO e o TERMINAL"""
        
        #self._configurar_grafico(cenario) # LIGA A JANELA DO GRÁFICO
        
        self._configurar_grafico(cenario)    # LIGA A JANELA DO GRÁFICO
        self._configurar_tabela_log()        # LIGA A JANELA DA TABELA
        print("\n=======================================================")
        print(" 🤖      CENTRAL DE CONTROLE ROBOSOCO 5001      🤖")
        print("         (MISSÃO EM MODO 100% AUTOMÁTICO)")
        print("=======================================================")
        print(f"Iniciando missão no cenário: {cenario.tipo_acidente.upper()} no túnel.")
        
        # Loop principal da missão
        while self.missao_ativa and robo.executar_passo_missao(cenario):
            sleep(0.54) # Pausa para simular tempo real (4.5 min total)
            self.root_log.update() # Atualiza a janela da tabela
            if robo.status == "Bateria Esgotada":
                break
        
        # --- FIM DA MISSÃO ---
        print("\n=======================================================")
        print(" 🏁                MISSÃO ENCERRADA                🏁")
        print("=======================================================")
        print(f"Relatório final: {len(self.log_missao)} pacotes de dados recebidos.")
        fotos_tiradas = [log for log in self.log_missao if 'confirmacao_foto' in log]
        if fotos_tiradas:
            print("\n--- Fotos Térmicas Registradas ---")
            for foto_log in fotos_tiradas:
                foto_id = foto_log['confirmacao_foto']['id']
                dados_foto = foto_log['confirmacao_foto']['dados']
                print(f"  - {foto_id}: Temp Max: {dados_foto['temp_max_registrada']}°C, Vítima: {dados_foto['dados_vitima']}")
        
        # (Etapa 3) Visualização Final
        plt.ioff()
        print("\nVisualização final do mapa da missão. Pode fechar a janela do gráfico.")
        plt.show() 

    def _on_closing_log_window(self):
        """Chamado quando a janela de log é fechada pelo usuário."""
        print("[Central] Janela de log fechada. Encerrando a missão...")
        self.missao_ativa = False # Sinaliza para o loop principal parar
        if self.root_log:
            self.root_log.destroy()
            self.root_log = None

    def _adicionar_log_tabela(self, fonte, mensagem, acao_ia=""):
        """Adiciona uma nova entrada na tabela de log."""
        # Verifica se a janela/tabela ainda existem antes de tentar inserir
        if self.root_log and self.tree_log:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            self.tree_log.insert("", tk.END, values=(timestamp, fonte, mensagem, acao_ia))
            self.tree_log.yview_moveto(1) # Auto-scroll para o final

    def receber_dados_robo(self, pacote_dados):
        """ 
        ESTA É A NOVA CENTRAL AUTOMÁTICA.
        Ela recebe dados e decide o que fazer.
        """
        
        # --- 1. Extrai Dados do Pacote ---
        pos_x = pacote_dados['pos_x']
        bateria = pacote_dados['bateria']
        status = pacote_dados['status_robo']
        sensores = pacote_dados['sensores']
        temp = sensores['temp']
        vitima = sensores['vitima_detectada']
        risco = sensores['risco_estrutural']

        alerta_vitima_grafico = False # Flag para desenhar o 'X'
        comando_final = None          # Comando a ser enviado ao robô
        mensagem_log = f"Ponto {pos_x}m | Bat: {bateria}% | Status: {status} | Temp: {temp}°C"
        acao_log = ""

        # --- 2. Lógica de Risco Imediato (IGNORA TODO O RESTO) ---
        if risco > 3:
            print(f"  🚧 ALERTA ESTRUTURAL (Nível {risco})! Acionando RETORNO AUTOMÁTICO.")
            msg = f"ALERTA ESTRUTURAL (Nível {risco})! Acionando RETORNO AUTOMÁTICO."
            self._adicionar_log_tabela("IA Central", msg, "RETORNAR_BASE")
            comando_final = {'acao': 'RETORNAR_BASE'}
        elif temp > 1000: # Limite de temperatura aumentado para ignorar o fogo e completar a missão
            msg = f"ALERTA DE TEMPERATURA ({temp}°C)! Acionando RETORNO AUTOMÁTICO."
            self._adicionar_log_tabela("IA Central", msg, "RETORNAR_BASE")
            comando_final = {'acao': 'RETORNAR_BASE'}
        elif status == "Retornando":
            # Se o robô já está voltando (por bateria baixa ou comando), a central só monitora.
            mensagem_log = f"🔋 RETORNANDO À BASE | Ponto {pos_x}m | Bat: {bateria}%"
            acao_log = "MONITORANDO RETORNO"
            # Nenhum comando novo é necessário
        
        if comando_final: # Se um comando de risco foi dado, pule o resto
            return comando_final
        # --- 3. Lógica de Sequência Automática (SE NÃO HÁ RISCO IMEDIATO) ---
        elif status == "Aguardando":
            # O Robô está parado, esperando o *próximo passo* da sequência.
            if self.estado_automatico.get('em_sequencia') == True:
                proximo_passo = self.estado_automatico.get('proximo_passo')
                if proximo_passo:
                    print(f"[Central Automática] Ação anterior concluída. Executando próximo passo: {proximo_passo.get('acao')}")
                    comando_final = {'acao': proximo_passo.get('acao')}
                    # Atualiza a sequência para o passo seguinte, se houver
                    self.estado_automatico['proximo_passo'] = proximo_passo.get('proximo_passo')
                else:
                    self.estado_automatico = {} # A sequência terminou, limpa o estado
            
        elif status == "Explorando":
            # O Robô está andando, procurando por NOVOS alertas.
            if vitima:
                pos_tuple = tuple(vitima['pos'])
                
                # Checa a "MEMÓRIA"
                if pos_tuple not in self.vitimas_registradas:
                    # --- VÍTIMA NOVA ENCONTRADA! ---
                    self.vitimas_registradas.add(pos_tuple) # Adiciona na memória
                    alerta_vitima_grafico = True # Manda o gráfico desenhar o 'X'
                    condicao_vitima = f"Estado: {vitima['estado_vital']}, {vitima['consciencia']}, {vitima['condicao']}"
                    
                    distancia = pos_x
                    tempo_chegada_min = round(distancia / 50) 

                    # Usa o modelo de IA para definir a prioridade
                    prioridade = self._prever_prioridade_vitima(vitima)

                    if prioridade == 1: # Prioridade Alta
                        print(f"  🚨 ALERTA DE VÍTIMA (PRIORIDADE ALTA) NO PONTO {pos_x}m!")
                        print(f"     Detalhes: {condicao_vitima}")
                        print(f"     Acionando Sequência: [KIT PRIMEIROS SOCORROS] -> [FOTO] -> [CONTINUAR]")
                        print(f"     Equipe de socorro chegará em {tempo_chegada_min} min.")
                        mensagem_log = f"🚨 VÍTIMA (PRIORIDADE ALTA) em {pos_x}m. Detalhes: {condicao_vitima}"
                        acao_log = "SOLTAR_KIT -> FOTO -> CONTINUAR"
                        self._adicionar_log_tabela("IA Central", f"Equipe de socorro chegará em {tempo_chegada_min} min.", "")

                        # Define a sequência de ações
                        passo2 = {'acao': 'REGISTRAR_FOTO_TERMICA'}
                        passo3 = {'acao': 'CONTINUAR_EXPLORACAO'}
                        passo2['proximo_passo'] = passo3 # Aninha o passo 3 dentro do passo 2
                        self.estado_automatico = {'em_sequencia': True, 'proximo_passo': passo2}
                        comando_final = {'acao': 'SOLTAR_KIT_PRIMEIROS_SOCORROS'}

                        if vitima['condicao'] == 'sangramento':
                            print("     PRIORIDADE MÁXIMA: Vítima com sangramento detectado!")
                            self._adicionar_log_tabela("IA Central", "PRIORIDADE MÁXIMA: Vítima com sangramento detectado!", "")
                        
                    elif prioridade == 2: # Prioridade Média
                        print(f"  ⚠️ ALERTA DE VÍTIMA (PRIORIDADE MÉDIA) NO PONTO {pos_x}m.")
                        print(f"     Detalhes: {condicao_vitima}")
                        print(f"     Acionando Sequência: [FOTO] -> [CONTINUAR EXPLORANDO]")
                        print(f"     Equipe de socorro chegará em {tempo_chegada_min} min.")
                        mensagem_log = f"⚠️ VÍTIMA (PRIORIDADE MÉDIA) em {pos_x}m. Detalhes: {condicao_vitima}"
                        acao_log = "FOTO -> CONTINUAR"
                        self._adicionar_log_tabela("IA Central", f"Equipe de socorro chegará em {tempo_chegada_min} min.", "")

                        # Define a sequência: FOTO e depois CONTINUAR
                        passo2 = {'acao': 'CONTINUAR_EXPLORACAO'}
                        self.estado_automatico = {'em_sequencia': True, 'proximo_passo': passo2}
                        comando_final = {'acao': 'REGISTRAR_FOTO_TERMICA'}
                
                else:
                    # Se a vítima já está na memória
                    print(f"[Central] Passando por vítima já registrada em {pos_tuple}...")
                    mensagem_log = f"Passando por vítima já registrada em {pos_tuple}."
                    
            elif status == "Fim do Túnel":
                print(f"  🏁 INFO: Robô chegou ao fim dos {pos_x}m do túnel.")
                mensagem_log = f"🏁 Robô chegou ao fim dos {pos_x}m do túnel."
                acao_log = "MANTER_POSICAO"
                comando_final = {'acao': 'MANTER_POSICAO'}
                
        # --- 4. Atualiza o Gráfico e Envia o Comando ---
        self._atualizar_grafico(pacote_dados, alerta_vitima=alerta_vitima_grafico)
        
        # Imprime o status básico (para não poluir)
        if not alerta_vitima_grafico and status == "Explorando" and comando_final is None:
             print(f"[Central] Ponto {pos_x}m | Bat: {bateria}% | Status: {status} | Temp: {temp}°C")

        # Adiciona a linha de log na tabela
        if not acao_log:
            acao_log = comando_final['acao'] if comando_final else "CONTINUAR_EXPLORACAO"
        
        self._adicionar_log_tabela("Robô", mensagem_log, acao_log)
        
        return comando_final

    def confirmar_registro_foto(self, foto_id, conteudo_foto):
        """ (TERMINAL) Loga a confirmação da foto. """
        print(f"[Central Automática] Confirmação recebida: Foto '{foto_id}' armazenada.")
        self.log_missao.append({
            'timestamp': datetime.datetime.now().isoformat(),
            'confirmacao_foto': {'id': foto_id, 'dados': conteudo_foto}
        })

# --- EXECUÇÃO PRINCIPAL DA SIMULAÇÃO ---
if __name__ == "__main__":

    # Criação dos componentes
    # Agora o programa inicia diretamente com o cenário da Linha Amarela
    cenario_tunel = Cenario(comprimento=500)
    central = CentralDeControle()
    robo = Robo(central_controle=central)

    # Inicia a simulação (que vai abrir o gráfico e rodar no terminal)
    central.iniciar_missao(robo, cenario_tunel)