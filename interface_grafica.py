import tkinter as tk
from tkinter import scrolledtext, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from operacoes import Operacoes, RPCServerNotFound
from config import SERVIDOR_IP, SERVIDOR_PORTA
from datetime import datetime

class BootstrapRPCGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora RPC Avançada")
        self.root.geometry("1300x850")
        self.fullscreen = True
        self.root.attributes('-fullscreen', self.fullscreen)
        
        self.style = tb.Style(theme="darkly") # Configurar tema Bootstrap
        # Cria um estilo customizado para botões grandes
        self.style.configure("Large.TButton", font=("Segoe UI", 20, "bold"))
        self.style.configure('.', font=('Segoe UI', 14))
        self.rpc = Operacoes()
        self.active_entry = None
        self.setup_ui()
        self.bind_focus_events()
    
    def setup_ui(self):
        # Frame principal
        main_frame = tb.Frame(self.root, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid principal
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 1. CABEÇALHO
        header_frame = tb.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = tb.Label(header_frame, text="Calculadora RPC",font=("Segoe UI", 20, "bold"),bootstyle="info")
        
        title_label.pack(side=tk.LEFT)
        
        # Frame para o lado direito (conectado + botão X)
        right_frame = tb.Frame(header_frame)
        right_frame.pack(side=tk.RIGHT)
        
        subtitle_label = tb.Label(right_frame, 
                                text=f"Conectado a: {SERVIDOR_IP}:{SERVIDOR_PORTA}",
                                font=("Segoe UI", 14),
                                bootstyle="light")
        subtitle_label.pack(side=tk.LEFT, padx=(0, 80))  # espaçamento para o botão
        
        # Botão X para sair do fullscreen ou fechar
        # Criar botões independentemente do fullscreen inicial
        self.toggle_button = tb.Button(
            right_frame, text="[]", width=3, bootstyle="light", command=self.toggle_fullscreen
        )
        self.exit_button = tb.Button(
            right_frame, text="X", width=3, bootstyle="danger", command=self.exit_fullscreen
        )

        # Mostrar somente se fullscreen for True
        if self.fullscreen:
            self.toggle_button.pack(side=tk.LEFT, padx=(0, 10))
            self.exit_button.pack(side=tk.LEFT, padx=(10, 0))
 
        # 2. OPERAÇÕES DISPONÍVEIS
        operation_frame = tb.Labelframe(
            main_frame, text="Operações Disponíveis", padding=10, bootstyle="info"
        )
        operation_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        self.selected_operation = tk.StringVar(value="soma")
        operations = [
            ("Soma", "soma"),
            ("Subtração", "subtracao"),
            ("Multiplicação", "produto"),
            ("Divisão", "divisao"),
            ("Fatorial", "fatorial"),
            ("Potência", "potencia"),
            ("Raiz Quadrada", "raiz_quadrada"),
            ("Resolução de Problemas", "math_problem_solver"),
            ("Últimas Notícias", "ultimas_noticias")
        ]

        # Configura todas as colunas para se expandirem igualmente
        for col in range(len(operations)):
            operation_frame.columnconfigure(col, weight=1)

        # Criar botões todos na mesma linha
        for i, (text, value) in enumerate(operations):
            btn = tb.Radiobutton(
                operation_frame,
                text=text,
                variable=self.selected_operation,
                value=value,
                command=self.update_input_fields,
                bootstyle="success-outline-toolbutton",
            )
            
            btn.grid(
                row=0,      
                column=i,     
                padx=5,       
                pady=5,        
                sticky="ew",
                ipadx=10,
                ipady=5  
            )
    
        # 3. SEÇÃO CENTRAL: Entrada + Teclado + Botões
        center_frame = tb.Frame(main_frame)
        center_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        center_frame.columnconfigure(0, weight=2)
        center_frame.columnconfigure(1, weight=1)
        
        # 3.1. COLUNA ESQUERDA: Entrada + Teclado
        left_column = tb.Frame(center_frame)
        left_column.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 20))
        
        # Frame de entrada de dados
        input_card = tb.Labelframe(left_column, text="Entrada de Dados", padding=20, bootstyle="light")
        input_card.pack(fill=tk.BOTH, expand=True)
        
        # Container para os campos de entrada
        entry_container = tb.Frame(input_card)
        entry_container.pack(fill=tk.X, pady=(0, 15))
        
        # Campo para múltiplos números
        self.numbers_label = tb.Label(entry_container, text="Números (separados por espaço):")
        self.numbers_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.numbers_entry = tb.Entry(entry_container, bootstyle="primary", width=50)
        self.numbers_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.numbers_entry.bind('<FocusIn>', lambda e: self.set_active_entry(self.numbers_entry))
        
        # Campo para problema matemático
        self.problem_label = tb.Label(entry_container, text="Problema Matemático:")
        self.problem_label.pack(side=tk.LEFT, padx=(0, 10))
        self.problem_label.pack_forget()
        
        self.problem_entry = tb.Entry(entry_container, bootstyle="primary", width=50)
        self.problem_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.problem_entry.pack_forget()
        self.problem_entry.bind('<FocusIn>', lambda e: self.set_active_entry(self.problem_entry))
        
        # Campo para quantidade de notícias
        self.news_label = tb.Label(entry_container, text="Quantidade de Notícias:")
        self.news_label.pack(side=tk.LEFT, padx=(0, 10))
        self.news_label.pack_forget()
        
        self.news_spinbox = tb.Spinbox(entry_container, from_=1, to=20, 
                                      bootstyle="primary", width=15)
        self.news_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        self.news_spinbox.pack_forget()
        self.news_spinbox.set(5)
        self.news_spinbox.bind('<FocusIn>', lambda e: self.set_active_entry(self.news_spinbox))
        
        # TECLADO NUMÉRICO DENTRO DO FRAME DE ENTRADA
        keyboard_frame = tb.Frame(input_card)
        keyboard_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label do teclado
        keyboard_label = tb.Label(keyboard_frame, text="Teclado Virtual:",
                                 font=("Segoe UI", 16, "bold"))
        keyboard_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Frame para os botões do teclado
        keys_frame = tb.Frame(keyboard_frame)
        keys_frame.pack(fill=tk.BOTH, expand=True)
        
        # Layout do teclado 4x5
        key_layout = [
            ['1', '2', '3', '+', '⌫'],
            ['4', '5', '6', '-', 'C'],
            ['7', '8', '9', '*', '='],
            ['0', '.', '/', '^', '!']
        ]
        
        # Configurar grid do teclado
        for i in range(5):
            keys_frame.columnconfigure(i, weight=1)
        for i in range(4):
            keys_frame.rowconfigure(i, weight=1)
        
        # Botões do teclado
        for row_idx, row_keys in enumerate(key_layout):
            for col_idx, key in enumerate(row_keys):
                if key:
                    if key in ['⌫', 'C', '=']:
                        btn_style = "danger" if key == 'C' else "warning" if key == '=' else "light"
                    else:
                        btn_style = "secondary"

                    btn = tb.Button(
                        keys_frame,text=key,
                        bootstyle=btn_style,padding=(15, 10),
                        command=lambda k=key: self.on_key_press(k)
                )
                    btn.grid(row=row_idx, column=col_idx, padx=1, pady=1, sticky='nsew')
        
        # 3.2. COLUNA DIREITA: Botões de ação
        right_column = tb.Frame(center_frame)
        right_column.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Container dos botões
        buttons_card = tb.Labelframe(right_column, text="Ações", padding=10, bootstyle="success")
        buttons_card.pack(fill=tk.BOTH, expand=True)
        
        # Botão principal de calcular
        self.calc_button = tb.Button(buttons_card, text="CALCULAR", 
                                    command=self.calculate, bootstyle="success",
                                    padding=(20, 15))
        self.calc_button.pack(fill=tk.X, pady=(0, 15))
        
        # Botões secundários
        secondary_buttons = [
            ("Limpar Campo", self.clear_current_field, "outline-info"),
            ("Limpar Tudo", self.clear_all_fields, "outline-info"),
            ("Copiar Resultado", self.copy_result, "primary-toolbutton"),
            ("Salvar Histórico", self.save_history, "primary"),
        ]
        
        for text, command, style in secondary_buttons:
            btn = tb.Button(buttons_card, text=text, command=command, 
                          bootstyle=style, padding=(15, 10))
            btn.pack(fill=tk.X, pady=8)
        
        # Botão Sobre
        about_btn = tb.Button(buttons_card, text="Sobre", command=self.show_about,
                            bootstyle="outline-warning", padding=(15, 10))
        about_btn.pack(fill=tk.X, pady=(15, 0))
        
        # 4. ÁREA DE RESULTADO E HISTÓRICO
        result_frame = tb.Labelframe(main_frame, text="Histórico de Resultados", 
                                    padding=10, bootstyle="light")
        result_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Controles do histórico
        history_controls = tb.Frame(result_frame)
        history_controls.pack(fill=tk.X, pady=(0, 15))
        
        # Botão Limpar Histórico
        clear_history_btn = tb.Button(history_controls, text="Limpar Histórico", 
                                     command=self.clear_history, bootstyle="outline-danger",
                                     padding=(12, 8))
        clear_history_btn.pack(side=tk.LEFT, padx=5)
        
        # Botão Exportar
        export_btn = tb.Button(history_controls, text="Exportar...", 
                              command=self.export_history, bootstyle="outline-warning",
                              padding=(12, 8))
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Área de texto para resultados
        self.result_text = scrolledtext.ScrolledText(result_frame, height=30,
                                                    wrap=tk.WORD, 
                                                    font=("Consolas", 20),
                                                    relief="flat", borderwidth=0)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Configurar tags para formatação
        self.result_text.tag_configure("timestamp", foreground="#adb5bd", 
                                      font=("Consolas", 12, "italic"))
        self.result_text.tag_configure("operation", foreground="#5bc0de", 
                                      font=("Consolas", 14, "bold"))
        self.result_text.tag_configure("input", foreground="#20c997", 
                                      font=("Consolas", 14))
        self.result_text.tag_configure("result", foreground="#e9ecef", 
                                      font=("Consolas", 14, "bold"))
        self.result_text.tag_configure("separator", foreground="#6C737A")
        self.result_text.tag_configure("error", foreground="#ff6b6b")
        self.result_text.tag_configure("success", foreground="#51cf66")
        
        # 5. BARRA DE STATUS
        status_frame = tb.Frame(main_frame, bootstyle="dark")
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Pronto para calcular. Campo ativo: Nenhum")
        status_label = tb.Label(status_frame, textvariable=self.status_var, 
                               bootstyle="inverse-dark",
                               padding=(15, 8))
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Indicador de conexão
        self.connection_status = tb.Label(status_frame, text="● CONECTADO", 
                                         bootstyle="success-inverse",
                                         padding=(15, 8))
        self.connection_status.pack(side=tk.RIGHT)
        
        # Atualizar campos inicialmente
        self.update_input_fields()
        
        # Definir entrada inicial como ativa
        self.set_active_entry(self.numbers_entry)
        
        # Adicionar histórico inicial
        self.add_initial_history()
    
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        
        if self.fullscreen:
            self.toggle_button.pack(side=tk.LEFT, padx=(0, 10))
            self.exit_button.pack(side=tk.LEFT, padx=(10, 0))
        else:
            self.toggle_button.pack_forget()
            self.exit_button.pack_forget()
    
    def exit_fullscreen(self):
        self.root.destroy()

    
    def add_initial_history(self):
        """Adiciona o histórico inicial formatado"""
        self.result_text.insert(tk.END, "_" * 60 + "\n\n", "separator")
        self.result_text.insert(tk.END, "HISTÓRICO DE CÁLCULOS\n", "operation")
        self.result_text.insert(tk.END, "_" * 60 + "\n\n", "separator")
        self.result_text.insert(tk.END, "Resultados aparecerão aqui...\n\n", "input")
        self.result_text.see(tk.END)
    
    def bind_focus_events(self):
        """Vincular eventos de foco a todos os campos de entrada"""
        entries = [self.numbers_entry, self.problem_entry, self.news_spinbox]
        for entry in entries:
            entry.bind('<FocusIn>', lambda e, widget=entry: self.set_active_entry(widget))
    
    def set_active_entry(self, widget):
        """Define qual campo de entrada está ativo"""
        self.active_entry = widget
        
        # Atualizar barra de status
        if widget == self.numbers_entry:
            self.status_var.set("Campo ativo: Números")
        elif widget == self.problem_entry:
            self.status_var.set("Campo ativo: Problema Matemático")
        elif widget == self.news_spinbox:
            self.status_var.set("Campo ativo: Quantidade de Notícias")
    
    def update_input_fields(self):
        """Atualiza os campos de entrada com base na operação selecionada"""
        operation = self.selected_operation.get()
        
        # Esconder todos os campos primeiro
        self.numbers_label.pack_forget()
        self.numbers_entry.pack_forget()
        self.problem_label.pack_forget()
        self.problem_entry.pack_forget()
        self.news_label.pack_forget()
        self.news_spinbox.pack_forget()
        
        # Mostrar campos apropriados
        if operation == 'math_problem_solver':
            self.problem_label.pack(side=tk.LEFT, padx=(0, 10))
            self.problem_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            self.set_active_entry(self.problem_entry)
            self.calc_button.config(text="RESOLVER PROBLEMA")
            self.status_var.set("Modo: Resolução de Problemas")
        elif operation == 'ultimas_noticias':
            self.news_label.pack(side=tk.LEFT, padx=(0, 10))
            self.news_spinbox.pack(side=tk.LEFT, padx=(0, 10))
            self.set_active_entry(self.news_spinbox)
            self.calc_button.config(text="BUSCAR NOTÍCIAS")
            self.status_var.set("Modo: Busca de Notícias")
        else:
            self.numbers_label.pack(side=tk.LEFT, padx=(0, 10))
            self.numbers_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            self.set_active_entry(self.numbers_entry)
            self.calc_button.config(text="CALCULAR")
            
            # Atualizar label com base na operação
            if operation == 'fatorial':
                self.numbers_label.config(text="Número inteiro:")
                self.status_var.set("Modo: Cálculo de Fatorial")
            elif operation == 'potencia':
                self.numbers_label.config(text="Base e Expoente (separados por espaço):")
                self.status_var.set("Modo: Cálculo de Potência")
            elif operation == 'raiz_quadrada':
                self.numbers_label.config(text="Número:")
                self.status_var.set("Modo: Cálculo de Raiz Quadrada")
            elif operation in ['soma', 'subtracao', 'produto', 'divisao']:
                self.numbers_label.config(text="Números (separados por espaço):")
                self.status_var.set(f"Modo: {operation.capitalize()}")
    
    def on_key_press(self, key):
        """Lida com pressionamento de teclas do teclado virtual"""
        if not self.active_entry:
            return
            
        current_text = self.active_entry.get()
        cursor_pos = self.active_entry.index(tk.INSERT)
        
        if key == '⌫':  # Backspace
            if current_text and cursor_pos > 0:
                new_text = current_text[:cursor_pos-1] + current_text[cursor_pos:]
                self.active_entry.delete(0, tk.END)
                self.active_entry.insert(0, new_text)
                self.active_entry.icursor(cursor_pos - 1)
                
        elif key == 'C': 
            self.active_entry.delete(0, tk.END)
            
        elif key == '=': 
            self.calculate()
            
        elif key == '^':  
            self.insert_at_cursor('^')
            
        elif key == '!': 
            self.insert_at_cursor('!')
            
        else: 
            self.insert_at_cursor(key)
    
    def insert_at_cursor(self, text):
        """Insere texto na posição do cursor"""
        if not self.active_entry:
            return
            
        cursor_pos = self.active_entry.index(tk.INSERT)
        current_text = self.active_entry.get()
        
        # Inserir na posição do cursor
        new_text = current_text[:cursor_pos] + text + current_text[cursor_pos:]
        self.active_entry.delete(0, tk.END)
        self.active_entry.insert(0, new_text)
        
        # Mover cursor para após o texto inserido
        self.active_entry.icursor(cursor_pos + len(text))
    
    def calculate(self):
        """Executa a operação selecionada"""
        operation = self.selected_operation.get()
        
        try:
            if operation == 'math_problem_solver':
                problema = self.problem_entry.get().strip()
                if not problema:
                    messagebox.showwarning("Entrada vazia", "Por favor, digite um problema matemático.")
                    return
                
                self.status_var.set(f"Resolvendo problema: {problema[:30]}...")
                resultado = self.rpc.math_problem_solver(problema)
                
            elif operation == 'ultimas_noticias':
                try:
                    qtd = int(self.news_spinbox.get())
                    if qtd < 1 or qtd > 20:
                        messagebox.showwarning("Valor inválido", "A quantidade deve estar entre 1 e 20.")
                        return
                except ValueError:
                    messagebox.showwarning("Valor inválido", "Digite um número válido para a quantidade.")
                    return
                
                self.status_var.set(f"Buscando {qtd} notícias...")
                resultado = self.rpc.ultimas_noticias(qtd)
                
            else:
                # Operações matemáticas
                nums_text = self.numbers_entry.get().strip()
                if not nums_text:
                    messagebox.showwarning("Entrada vazia", "Por favor, digite os números.")
                    return
                
                self.status_var.set(f"Calculando {operation}...")
                
                if operation == 'fatorial':
                    try:
                        n = int(float(nums_text))
                        resultado = self.rpc.fatorial(n)
                    except ValueError:
                        messagebox.showwarning("Valor inválido", "Digite um número inteiro válido.")
                        return
                    
                elif operation == 'potencia':
                    nums = nums_text.split()
                    if len(nums) != 2:
                        messagebox.showwarning("Entrada inválida", "Digite base e expoente separados por espaço.")
                        return
                    try:
                        base = float(nums[0])
                        exp = float(nums[1])
                        resultado = self.rpc.potencia(base, exp)
                    except ValueError:
                        messagebox.showwarning("Valor inválido", "Digite números válidos.")
                        return
                    
                elif operation == 'raiz_quadrada':
                    try:
                        n = float(nums_text)
                        if n < 0:
                            messagebox.showwarning("Valor inválido", "Não é possível calcular raiz de número negativo.")
                            return
                        resultado = self.rpc.raiz_quadrada(n)
                    except ValueError:
                        messagebox.showwarning("Valor inválido", "Digite um número válido.")
                        return
                    
                else:
                    nums = nums_text.split()
                    if len(nums) < 2:
                        messagebox.showwarning("Entrada inválida", "Digite pelo menos dois números.")
                        return
                    
                    try:
                        nums_float = list(map(float, nums))
                    except ValueError:
                        messagebox.showwarning("Valor inválido", "Digite números válidos.")
                        return
                    
                    if operation == 'soma':
                        resultado = self.rpc.soma(*nums_float)
                    elif operation == 'subtracao':
                        resultado = self.rpc.subtracao(*nums_float)
                    elif operation == 'produto':
                        resultado = self.rpc.produto(*nums_float)
                    elif operation == 'divisao':
                        # Verificar divisão por zero
                        if 0 in nums_float[1:]:
                            messagebox.showwarning("Divisão por zero", "Não é possível dividir por zero.")
                            return
                        resultado = self.rpc.divisao(*nums_float)
            
            # Exibir resultado formatado
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Adicionar separador
            self.result_text.insert(tk.END, "-" * 60 + "\n", "separator")
            
            # Timestamp
            self.result_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
            
            # Operação
            operation_names = {
                'soma': 'SOMA',
                'subtracao': 'SUBTRAÇÃO',
                'produto': 'MULTIPLICAÇÃO',
                'divisao': 'DIVISÃO',
                'fatorial': 'FATORIAL',
                'potencia': 'POTÊNCIA',
                'raiz_quadrada': 'RAIZ QUADRADA',
                'math_problem_solver': 'RESOLUÇÃO DE PROBLEMAS',
                'ultimas_noticias': 'ÚLTIMAS NOTÍCIAS'
            }
            
            self.result_text.insert(tk.END, f"{operation_names.get(operation, operation.upper())}\n", "operation")
            
            # Entrada usada
            if operation == 'math_problem_solver':
                self.result_text.insert(tk.END, f"Problema: {self.problem_entry.get()}\n", "input")
            elif operation == 'ultimas_noticias':
                self.result_text.insert(tk.END, f"Quantidade: {self.news_spinbox.get()}\n", "input")
            else:
                if operation == 'fatorial':
                    self.result_text.insert(tk.END, f"Entrada: {self.numbers_entry.get()}!\n", "input")
                elif operation == 'potencia':
                    nums = self.numbers_entry.get().split()
                    if len(nums) == 2:
                        self.result_text.insert(tk.END, f"Entrada: {nums[0]}^{nums[1]}\n", "input")
                else:
                    self.result_text.insert(tk.END, f"Entrada: {self.numbers_entry.get()}\n", "input")
            
            # Resultado formatado
            if operation == 'ultimas_noticias' and isinstance(resultado, list):
                self.result_text.insert(tk.END, f"Notícias encontradas: {len(resultado)}\n", "result")
                for i, item in enumerate(resultado, 1):
                    if isinstance(item, dict):
                        self.result_text.insert(tk.END, f"  {i}. {item.get('titulo', 'Sem título')}\n")
                        if item.get('link'):
                            self.result_text.insert(tk.END, f"     Link: {item['link']}\n", "timestamp")
                    else:
                        self.result_text.insert(tk.END, f"  {i}. {item}\n")
            else:
                self.result_text.insert(tk.END, f"Resultado: {resultado}\n", "result")
            
            self.result_text.see(tk.END)
            self.status_var.set("Operação concluída com sucesso!")
            
        except RPCServerNotFound as e:
            messagebox.showerror("Erro de Conexão", 
                               f"Não foi possível conectar ao servidor RPC.\n"
                               f"Certifique-se de que o servidor está rodando em {SERVIDOR_IP}:{SERVIDOR_PORTA}")
            self.status_var.set("Erro: Servidor não encontrado")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
            self.status_var.set(f"Erro: {str(e)[:30]}")
    
    def clear_current_field(self):
        """Limpa apenas o campo ativo"""
        if self.active_entry:
            self.active_entry.delete(0, tk.END)
            self.status_var.set("Campo limpo")
    
    def clear_all_fields(self):
        """Limpa todos os campos de entrada"""
        self.numbers_entry.delete(0, tk.END)
        self.problem_entry.delete(0, tk.END)
        self.news_spinbox.set(5)
        self.status_var.set("Todos os campos limpos")
    
    def clear_history(self):
        """Limpa o histórico de resultados"""
        if messagebox.askyesno("Limpar Histórico", "Tem certeza que deseja limpar todo o histórico?"):
            self.result_text.delete(1.0, tk.END)
            self.add_initial_history()
            self.status_var.set("Histórico limpo")
    
    def save_history(self):
        """Salva o histórico em um arquivo"""
        from tkinter import filedialog
        import os
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="historico_calculos.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.result_text.get(1.0, tk.END))
                self.status_var.set(f"Histórico salvo: {os.path.basename(filename)}")
                messagebox.showinfo("Sucesso", f"Histórico salvo em:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível salvar o arquivo:\n{str(e)}")
    
    def export_history(self):
        """Exporta o histórico em diferentes formatos"""
        from tkinter import filedialog
        import json
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialfile="historico_calculos.json"
        )
        
        if filename:
            try:
                content = self.result_text.get(1.0, tk.END)
                
                if filename.endswith('.json'):
                    lines = content.strip().split('\n')
                    data = {"calculos": lines}
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                        
                elif filename.endswith('.csv'):
                    lines = content.strip().split('\n')
                    with open(filename, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(['Timestamp', 'Operação', 'Resultado'])
                        writer.writerow(['Export', 'Conteúdo', content[:100]])
                        
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                self.status_var.set(f"Exportado: {filename}")
                messagebox.showinfo("Sucesso", "Histórico exportado com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível exportar:\n{str(e)}")
    
    def copy_result(self):
        """Copia o resultado mais recente para a área de transferência"""
        try:
            content = self.result_text.get(1.0, tk.END)
            lines = content.strip().split('\n')
            
            last_result = ""
            for line in reversed(lines):
                if line.startswith("Resultado:") or "=" in line:
                    last_result = line
                    break
            
            if last_result:
                self.root.clipboard_clear()
                self.root.clipboard_append(last_result)
                self.status_var.set("Resultado copiado para a área de transferência")
            else:
                messagebox.showinfo("Informação", "Nenhum resultado encontrado para copiar.")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível copiar: {str(e)}")
    
    def show_about(self):
        """Exibe informações sobre o programa"""
        about_text = f"""Calculadora RPC

            Sistema de Calculadora Distribuída usando RPC (Remote Procedure Call)

            Funcionalidades:
            1. Operações matemáticas básicas (soma, subtração, etc.)
            2. Cálculos avançados (fatorial, potência, raiz quadrada)
            3. Resolução de problemas matemáticos usando IA
            4. Busca de notícias em tempo real
            5. Cache local para melhor desempenho
            6. Teclado virtual completo

            Configuração do servidor: {SERVIDOR_IP}:{SERVIDOR_PORTA}

            Instruções:
            1. Inicie o servidor: python servidor.py
            2. Use esta interface para executar operações
            3. Clique nos campos de entrada e use o teclado virtual
            4. Use ⌫ para apagar e C para limpar o campo ativo

            Desenvolvido com Python e ttkbootstrap"""
        
        messagebox.showinfo("Sobre", about_text)

def main():
    """Função principal para iniciar a interface gráfica"""
    root = tb.Window(themename="darkly")  
    app = BootstrapRPCGUI(root)
    
    def on_closing():
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Teclas de atalho
    root.bind('<Control-q>', lambda e: on_closing())
    root.bind('<Control-c>', lambda e: app.copy_result())
    root.bind('<Control-l>', lambda e: app.clear_all_fields())
    root.bind('<Return>', lambda e: app.calculate())
    
    # Centralizar a janela
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()