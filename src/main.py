import json
import os
import sys
import tkinter as tk
import uuid
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import colorchooser, messagebox, ttk

if getattr(sys, "frozen", False):
    PASTA_DADOS = Path(os.environ.get("APPDATA", Path.home())) / "Minha Agenda"
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    ARQUIVO_DADOS = PASTA_DADOS / "dados_agenda.json"
    PASTA_RECURSOS = Path(sys._MEIPASS)
else:
    ARQUIVO_DADOS = Path(__file__).with_name("dados_agenda.json")
    PASTA_RECURSOS = Path(__file__).parent.parent

ARQUIVO_WALLPAPER = PASTA_RECURSOS / "assets" / "falling_from_heaven.png"
HORAS = [f"{hora:02d}:00" for hora in range(24)]
COR_PAINEL = "#0A0A0A"
COR_PAINEL_SECUNDARIA = "#111111"


class AgendaApp:
    def __init__(self, janela):
        self.janela = janela
        janela.title("Minha Agenda")
        janela.geometry("1050x680")
        janela.minsize(820, 520)
        janela.configure(bg="#000000")
        janela.attributes("-alpha", 1.0)
        self.data_atual = date.today()
        self.visualizacao = tk.StringVar(value="Dia")
        self.data_revisao = date.today()
        self.visualizacao_revisao = tk.StringVar(value="Dia")
        self.modelos, self.tarefas, self.objetivos, self.revisoes, self.lembretes = self.carregar_dados()
        self.criar_tema()
        self.criar_fundo()
        self.criar_interface()
        self.atualizar_agenda()

    def criar_tema(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TFrame", background=COR_PAINEL)
        estilo.configure("TLabel", background=COR_PAINEL, foreground="#F3F3F3")
        estilo.configure("Titulo.TLabel", background=COR_PAINEL, foreground="#FFFFFF",
                         font=("Segoe UI", 18, "bold"))
        estilo.configure("Cabecalho.TLabel", background=COR_PAINEL, foreground="#FFFFFF",
                         font=("Segoe UI", 11, "bold"))
        estilo.configure("TButton", background="#202020", foreground="#FFFFFF", padding=6)
        estilo.map("TButton", background=[("active", "#333333")])
        estilo.configure("TRadiobutton", background=COR_PAINEL, foreground="#F3F3F3")
        estilo.map("TRadiobutton", background=[("active", COR_PAINEL)])
        estilo.configure("TCheckbutton", background=COR_PAINEL, foreground="#F3F3F3")
        estilo.map("TCheckbutton", background=[("active", COR_PAINEL)])
        estilo.configure("TEntry", fieldbackground="#181818", foreground="#FFFFFF")
        estilo.configure("TCombobox", fieldbackground="#181818", foreground="#FFFFFF")
        estilo.configure("TNotebook", background="#050505", borderwidth=0)
        estilo.configure("TNotebook.Tab", background="#181818", foreground="#DDDDDD", padding=(14, 7))
        estilo.map("TNotebook.Tab", background=[("selected", COR_PAINEL)],
                   foreground=[("selected", "#FFFFFF")])

    def criar_fundo(self):
        if not ARQUIVO_WALLPAPER.exists():
            return
        self.wallpaper_original = tk.PhotoImage(file=str(ARQUIVO_WALLPAPER))
        fator = max(1, min(self.wallpaper_original.width() // 1050,
                           self.wallpaper_original.height() // 680))
        self.wallpaper = self.wallpaper_original.subsample(fator, fator)
        fundo = tk.Label(self.janela, image=self.wallpaper, bg="#000000", borderwidth=0)
        fundo.place(relx=1, rely=1, anchor="se")

    def criar_interface(self):
        self.abas = ttk.Notebook(self.janela)
        self.abas.pack(fill="both", expand=True, padx=24, pady=24)
        pagina_agenda = ttk.Frame(self.abas)
        self.pagina_objetivos = ttk.Frame(self.abas)
        self.pagina_revisoes = ttk.Frame(self.abas)
        self.abas.add(pagina_agenda, text="Agenda")
        self.abas.add(self.pagina_objetivos, text="Objetivos")
        self.abas.add(self.pagina_revisoes, text="Repetição espaçada")

        cabecalho = ttk.Frame(pagina_agenda, padding=(18, 14))
        cabecalho.pack(fill="x")
        ttk.Button(cabecalho, text="‹", width=4, command=lambda: self.mover_data(-1)).pack(side="left")
        self.label_data = ttk.Label(cabecalho, style="Titulo.TLabel")
        self.label_data.pack(side="left", padx=18)
        ttk.Button(cabecalho, text="Hoje", command=self.ir_para_hoje).pack(side="left")
        ttk.Button(cabecalho, text="›", width=4, command=lambda: self.mover_data(1)).pack(side="left", padx=8)
        for texto in ("Semana", "Dia"):
            ttk.Radiobutton(cabecalho, text=texto, variable=self.visualizacao, value=texto,
                            command=self.atualizar_agenda).pack(side="right", padx=6)
        self.area_agenda = ttk.Frame(pagina_agenda, padding=(18, 4))
        self.area_agenda.pack(fill="both", expand=True)
        rodape = ttk.Frame(pagina_agenda, padding=(18, 14))
        rodape.pack(fill="x")
        ttk.Button(rodape, text="+ Adicionar tarefa", command=self.abrir_adicionar_tarefa).pack(side="left")
        ttk.Button(rodape, text="Modelos de tarefa", command=self.abrir_modelos).pack(side="left", padx=10)
        self.criar_pagina_objetivos()
        self.criar_pagina_revisoes()

    def carregar_dados(self):
        if not ARQUIVO_DADOS.exists():
            return [], [], [], [], []
        try:
            dados = json.loads(ARQUIVO_DADOS.read_text(encoding="utf-8"))
            return (dados.get("modelos", []), dados.get("tarefas", []),
                    dados.get("objetivos", []), dados.get("revisoes", []),
                    dados.get("lembretes", []))
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning("Aviso", "Não foi possível ler os dados salvos.")
            return [], [], [], [], []

    def salvar_dados(self):
        dados = {"modelos": self.modelos, "tarefas": self.tarefas,
                 "objetivos": self.objetivos, "revisoes": self.revisoes,
                 "lembretes": self.lembretes}
        ARQUIVO_DADOS.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")

    def criar_pagina_objetivos(self):
        cabecalho = ttk.Frame(self.pagina_objetivos, padding=(24, 22, 24, 12))
        cabecalho.pack(fill="x")
        ttk.Label(cabecalho, text="Objetivos de longo prazo", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(cabecalho, text="Registre o que deseja alcançar e acompanhe seu progresso.").pack(
            anchor="w", pady=(4, 0))

        formulario = ttk.Frame(self.pagina_objetivos, padding=(24, 8))
        formulario.pack(fill="x")
        ttk.Label(formulario, text="Objetivo").pack(side="left", padx=(0, 6))
        self.campo_objetivo = ttk.Entry(formulario)
        self.campo_objetivo.pack(side="left", fill="x", expand=True)
        self.campo_objetivo.bind("<Return>", lambda _e: self.adicionar_objetivo())
        ttk.Label(formulario, text="Prazo").pack(side="left", padx=(12, 6))
        self.campo_prazo = ttk.Entry(formulario, width=12)
        self.campo_prazo.insert(0, (date.today() + timedelta(days=365)).strftime("%d/%m/%Y"))
        self.campo_prazo.pack(side="left")
        ttk.Button(formulario, text="+ Adicionar objetivo", command=self.adicionar_objetivo).pack(
            side="left", padx=(10, 0))

        area = ttk.Frame(self.pagina_objetivos, padding=(24, 8))
        area.pack(fill="both", expand=True)
        self.canvas_objetivos = tk.Canvas(area, bg=COR_PAINEL_SECUNDARIA, highlightthickness=1,
                                          highlightbackground="#454545")
        barra = ttk.Scrollbar(area, orient="vertical", command=self.canvas_objetivos.yview)
        self.lista_objetivos = ttk.Frame(self.canvas_objetivos, padding=10)
        self.lista_objetivos.bind(
            "<Configure>", lambda _e: self.canvas_objetivos.configure(
                scrollregion=self.canvas_objetivos.bbox("all")))
        item = self.canvas_objetivos.create_window((0, 0), window=self.lista_objetivos, anchor="nw")
        self.canvas_objetivos.bind(
            "<Configure>", lambda e: self.canvas_objetivos.itemconfigure(item, width=e.width))
        self.canvas_objetivos.configure(yscrollcommand=barra.set)
        self.canvas_objetivos.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        rodape = ttk.Frame(self.pagina_objetivos, padding=(24, 8, 24, 18))
        rodape.pack(fill="x")
        ttk.Button(rodape, text="Excluir objetivos concluídos",
                   command=self.excluir_objetivos_concluidos).pack(side="right")
        self.atualizar_objetivos()

    def adicionar_objetivo(self):
        texto = self.campo_objetivo.get().strip()
        if not texto:
            messagebox.showwarning("Objetivo", "Digite um objetivo antes de adicionar.")
            return
        try:
            prazo = datetime.strptime(self.campo_prazo.get(), "%d/%m/%Y").date()
        except ValueError:
            messagebox.showerror("Prazo inválido", "Use o formato DD/MM/AAAA.")
            return
        objetivo = {"id": uuid.uuid4().hex, "texto": texto, "prazo": prazo.isoformat(),
                    "concluido": False}
        self.objetivos.append(objetivo)
        self.criar_lembretes_objetivo(objetivo)
        self.campo_objetivo.delete(0, "end")
        self.salvar_dados()
        self.atualizar_objetivos()
        self.atualizar_agenda()

    def atualizar_objetivos(self):
        for item in self.lista_objetivos.winfo_children():
            item.destroy()
        if not self.objetivos:
            ttk.Label(self.lista_objetivos, text="Nenhum objetivo adicionado.",
                      foreground="#777777").pack(pady=28)
            return
        for objetivo in self.objetivos:
            linha = ttk.Frame(self.lista_objetivos, padding=(5, 7))
            linha.pack(fill="x")
            marcado = tk.BooleanVar(value=objetivo.get("concluido", False))
            texto = objetivo["texto"]
            if objetivo.get("prazo"):
                prazo = date.fromisoformat(objetivo["prazo"]).strftime("%d/%m/%Y")
                texto = f"{texto}  •  prazo: {prazo}"
            if marcado.get():
                texto = f"✓ {texto}"
            check = ttk.Checkbutton(
                linha, text=texto, variable=marcado,
                command=lambda o=objetivo, v=marcado: self.alternar_objetivo(o, v.get()))
            check.pack(side="left", fill="x", expand=True)
            ttk.Button(linha, text="Alterar prazo" if objetivo.get("prazo") else "Definir prazo",
                       command=lambda o=objetivo: self.abrir_definir_prazo(o)).pack(side="right", padx=5)
            ttk.Button(linha, text="Excluir", command=lambda o=objetivo: self.excluir_objetivo(o)).pack(side="right")
            ttk.Separator(self.lista_objetivos).pack(fill="x")

    def abrir_definir_prazo(self, objetivo):
        janela = tk.Toplevel(self.janela)
        janela.title("Definir prazo")
        janela.resizable(False, False)
        corpo = ttk.Frame(janela, padding=18)
        corpo.pack()
        ttk.Label(corpo, text=objetivo["texto"], style="Cabecalho.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(0, 12))
        ttk.Label(corpo, text="Prazo (DD/MM/AAAA)").grid(row=1, column=0, padx=(0, 8))
        campo = ttk.Entry(corpo, width=14)
        prazo_atual = (date.fromisoformat(objetivo["prazo"]) if objetivo.get("prazo")
                       else date.today() + timedelta(days=365))
        campo.insert(0, prazo_atual.strftime("%d/%m/%Y"))
        campo.grid(row=1, column=1)
        campo.focus_set()

        def salvar():
            try:
                prazo = datetime.strptime(campo.get(), "%d/%m/%Y").date()
            except ValueError:
                messagebox.showerror("Prazo inválido", "Use o formato DD/MM/AAAA.", parent=janela)
                return
            self.remover_lembretes_objetivo(objetivo)
            objetivo.setdefault("id", uuid.uuid4().hex)
            objetivo["prazo"] = prazo.isoformat()
            if not objetivo.get("concluido", False):
                self.criar_lembretes_objetivo(objetivo)
            self.salvar_dados()
            janela.destroy()
            self.atualizar_objetivos()
            self.atualizar_agenda()

        ttk.Button(corpo, text="Salvar prazo", command=salvar).grid(
            row=2, column=1, sticky="e", pady=(14, 0))

    def alternar_objetivo(self, objetivo, concluido):
        objetivo["concluido"] = concluido
        if concluido:
            self.remover_lembretes_objetivo(objetivo)
        elif objetivo.get("prazo"):
            objetivo.setdefault("id", uuid.uuid4().hex)
            self.criar_lembretes_objetivo(objetivo)
        self.salvar_dados()
        self.atualizar_objetivos()
        self.atualizar_agenda()

    def excluir_objetivo(self, objetivo):
        if messagebox.askyesno("Excluir objetivo", f'Excluir "{objetivo["texto"]}"?'):
            self.remover_lembretes_objetivo(objetivo)
            self.objetivos.remove(objetivo)
            self.salvar_dados()
            self.atualizar_objetivos()
            self.atualizar_agenda()

    def excluir_objetivos_concluidos(self):
        concluidos = [o for o in self.objetivos if o.get("concluido", False)]
        if not concluidos:
            messagebox.showinfo("Objetivos", "Não há objetivos concluídos para excluir.")
            return
        if messagebox.askyesno("Excluir concluídos", f"Excluir {len(concluidos)} objetivo(s) concluído(s)?"):
            for objetivo in concluidos:
                self.remover_lembretes_objetivo(objetivo)
            self.objetivos = [o for o in self.objetivos if not o.get("concluido", False)]
            self.salvar_dados()
            self.atualizar_objetivos()
            self.atualizar_agenda()

    @staticmethod
    def subtrair_meses(data_base, meses):
        indice = data_base.year * 12 + data_base.month - 1 - meses
        ano, mes_zero = divmod(indice, 12)
        mes = mes_zero + 1
        dia = min(data_base.day, monthrange(ano, mes)[1])
        return date(ano, mes, dia)

    def criar_lembretes_objetivo(self, objetivo):
        prazo = date.fromisoformat(objetivo["prazo"])
        datas = [
            (self.subtrair_meses(prazo, 6), "6 meses"),
            (self.subtrair_meses(prazo, 3), "3 meses"),
            (self.subtrair_meses(prazo, 1), "1 mês"),
            (prazo - timedelta(weeks=2), "2 semanas"),
            (prazo - timedelta(weeks=1), "1 semana"),
            (prazo - timedelta(days=1), "1 dia"),
        ]
        for data_lembrete, antecedencia in datas:
            self.lembretes.append({"objetivo_id": objetivo["id"], "data": data_lembrete.isoformat(),
                                   "titulo": objetivo["texto"], "antecedencia": antecedencia})

    def remover_lembretes_objetivo(self, objetivo):
        objetivo_id = objetivo.get("id")
        if objetivo_id:
            self.lembretes = [l for l in self.lembretes if l.get("objetivo_id") != objetivo_id]

    def atualizar_agenda(self):
        for item in self.area_agenda.winfo_children():
            item.destroy()
        if self.visualizacao.get() == "Dia":
            self.label_data.config(text=self.data_atual.strftime("%d/%m/%Y"))
            self.mostrar_dia()
        else:
            inicio = self.data_atual - timedelta(days=self.data_atual.weekday())
            fim = inicio + timedelta(days=6)
            self.label_data.config(text=f"{inicio:%d/%m} – {fim:%d/%m/%Y}")
            self.mostrar_semana(inicio)

    def criar_area_rolavel(self):
        canvas = tk.Canvas(self.area_agenda, bg="#000000", highlightthickness=1,
                           highlightbackground="#454545")
        barra = ttk.Scrollbar(self.area_agenda, orient="vertical", command=canvas.yview)
        conteudo = tk.Frame(canvas, bg="#000000")
        if hasattr(self, "wallpaper"):
            fundo_horarios = tk.Label(conteudo, image=self.wallpaper, bg="#000000", borderwidth=0)
            fundo_horarios.place(relx=0.5, rely=0.5, anchor="center")
        conteudo.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        item = canvas.create_window((0, 0), window=conteudo, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(item, width=e.width))
        canvas.configure(yscrollcommand=barra.set)
        canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return conteudo

    def mostrar_dia(self):
        conteudo = self.criar_area_rolavel()
        tarefas = {t["hora"]: t for t in self.tarefas if t["data"] == self.data_atual.isoformat()}
        lembretes = [l for l in self.lembretes if l["data"] == self.data_atual.isoformat()]
        if lembretes:
            caixa_lembretes = ttk.Frame(conteudo, padding=(8, 5))
            caixa_lembretes.grid(row=0, column=0, columnspan=2, sticky="ew")
            for lembrete in lembretes:
                tk.Label(caixa_lembretes,
                         text=f'Lembrete: faltam {lembrete["antecedencia"]} para “{lembrete["titulo"]}”',
                         bg="#FFE59A", anchor="w", padx=10, pady=7,
                         font=("Segoe UI", 10, "bold")).pack(fill="x", pady=2)
        deslocamento = 1 if lembretes else 0
        for linha, hora in enumerate(HORAS):
            ttk.Label(conteudo, text=hora, width=7, foreground="#666").grid(
                row=linha + deslocamento, column=0, sticky="nw", padx=8, pady=10)
            tarefa = tarefas.get(hora)
            if tarefa:
                bloco = tk.Label(conteudo, text=tarefa["titulo"], bg=tarefa["cor"], anchor="w",
                                  padx=10, pady=7, font=("Segoe UI", 10, "bold"), cursor="hand2")
                bloco.grid(row=linha + deslocamento, column=1, sticky="ew", padx=(0, 8), pady=3)
                bloco.bind("<Button-3>", lambda _e, t=tarefa: self.excluir_tarefa(t))
            else:
                ttk.Separator(conteudo).grid(row=linha + deslocamento, column=1,
                                             sticky="ew", padx=(0, 8), pady=16)
        conteudo.columnconfigure(1, weight=1)

    def mostrar_semana(self, inicio):
        quadro = ttk.Frame(self.area_agenda, relief="solid", borderwidth=1)
        quadro.pack(fill="both", expand=True)
        nomes = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for coluna in range(7):
            dia = inicio + timedelta(days=coluna)
            ttk.Label(quadro, text=f"{nomes[coluna]}\n{dia:%d/%m}", style="Cabecalho.TLabel",
                      anchor="center").grid(row=0, column=coluna, sticky="ew", padx=3, pady=8)
            lista = tk.Frame(quadro, bg=COR_PAINEL_SECUNDARIA, padx=5, pady=5)
            lista.grid(row=1, column=coluna, sticky="nsew", padx=2, pady=(0, 3))
            tarefas = sorted((t for t in self.tarefas if t["data"] == dia.isoformat()),
                             key=lambda t: t["hora"])
            lembretes = [l for l in self.lembretes if l["data"] == dia.isoformat()]
            if not tarefas and not lembretes:
                tk.Label(lista, text="Sem tarefas", bg=COR_PAINEL_SECUNDARIA,
                         fg="#AAAAAA").pack(pady=12)
            for lembrete in lembretes:
                tk.Label(lista, text=f'Lembrete ({lembrete["antecedencia"]})\n{lembrete["titulo"]}',
                         bg="#FFE59A", anchor="w", justify="left", padx=6, pady=5,
                         wraplength=110).pack(fill="x", pady=3)
            for tarefa in tarefas:
                bloco = tk.Label(lista, text=f'{tarefa["hora"]}\n{tarefa["titulo"]}', bg=tarefa["cor"],
                                  anchor="w", justify="left", padx=6, pady=5, wraplength=110, cursor="hand2")
                bloco.pack(fill="x", pady=3)
                bloco.bind("<Button-3>", lambda _e, t=tarefa: self.excluir_tarefa(t))
            quadro.columnconfigure(coluna, weight=1, uniform="dias")
        quadro.rowconfigure(1, weight=1)

    def mover_data(self, direcao):
        passo = 7 if self.visualizacao.get() == "Semana" else 1
        self.data_atual += timedelta(days=direcao * passo)
        self.atualizar_agenda()

    def ir_para_hoje(self):
        self.data_atual = date.today()
        self.atualizar_agenda()

    def abrir_adicionar_tarefa(self):
        if not self.modelos:
            messagebox.showinfo("Modelos", "Crie um modelo antes de adicionar uma tarefa.")
            self.abrir_modelos()
            return
        janela = tk.Toplevel(self.janela)
        janela.title("Adicionar tarefa")
        janela.resizable(False, False)
        corpo = ttk.Frame(janela, padding=18)
        corpo.pack()
        ttk.Label(corpo, text="Modelo").grid(row=0, column=0, sticky="w", pady=6)
        modelo = ttk.Combobox(corpo, values=[m["titulo"] for m in self.modelos], state="readonly", width=28)
        modelo.current(0)
        modelo.grid(row=0, column=1, padx=8, pady=6)
        ttk.Label(corpo, text="Data").grid(row=1, column=0, sticky="w", pady=6)
        campo_data = ttk.Entry(corpo, width=31)
        campo_data.insert(0, self.data_atual.strftime("%d/%m/%Y"))
        campo_data.grid(row=1, column=1, padx=8, pady=6)
        ttk.Label(corpo, text="Hora").grid(row=2, column=0, sticky="w", pady=6)
        hora = ttk.Combobox(corpo, values=HORAS, state="readonly", width=28)
        hora.current(8)
        hora.grid(row=2, column=1, padx=8, pady=6)

        def adicionar():
            try:
                data_escolhida = datetime.strptime(campo_data.get(), "%d/%m/%Y").date()
            except ValueError:
                messagebox.showerror("Data inválida", "Use o formato DD/MM/AAAA.", parent=janela)
                return
            if any(t["data"] == data_escolhida.isoformat() and t["hora"] == hora.get() for t in self.tarefas):
                messagebox.showerror("Horário ocupado", "Já existe uma tarefa nesse horário.", parent=janela)
                return
            escolhido = self.modelos[modelo.current()]
            self.tarefas.append({"titulo": escolhido["titulo"], "cor": escolhido["cor"],
                                 "data": data_escolhida.isoformat(), "hora": hora.get()})
            self.salvar_dados()
            self.data_atual = data_escolhida
            janela.destroy()
            self.atualizar_agenda()

        ttk.Button(corpo, text="Adicionar", command=adicionar).grid(row=3, column=1, sticky="e", pady=(14, 0))

    def abrir_modelos(self):
        janela = tk.Toplevel(self.janela)
        janela.title("Modelos de tarefa")
        janela.geometry("430x370")
        corpo = ttk.Frame(janela, padding=16)
        corpo.pack(fill="both", expand=True)
        lista = tk.Listbox(corpo, height=10)
        lista.pack(fill="both", expand=True)

        def recarregar():
            lista.delete(0, "end")
            for item in self.modelos:
                lista.insert("end", item["titulo"])

        formulario = ttk.Frame(corpo)
        formulario.pack(fill="x", pady=(12, 0))
        titulo = ttk.Entry(formulario)
        titulo.pack(side="left", fill="x", expand=True)
        cor = tk.StringVar(value="#A8D8FF")

        def escolher_cor():
            escolhida = colorchooser.askcolor(cor.get(), parent=janela)[1]
            if escolhida:
                cor.set(escolhida)
                botao_cor.config(bg=escolhida)

        botao_cor = tk.Button(formulario, text="Cor", bg=cor.get(), command=escolher_cor)
        botao_cor.pack(side="left", padx=7)

        def criar():
            nome = titulo.get().strip()
            if not nome:
                messagebox.showwarning("Título", "Digite um título para o modelo.", parent=janela)
                return
            self.modelos.append({"titulo": nome, "cor": cor.get()})
            self.salvar_dados()
            titulo.delete(0, "end")
            recarregar()

        def excluir():
            selecao = lista.curselection()
            if selecao:
                del self.modelos[selecao[0]]
                self.salvar_dados()
                recarregar()

        ttk.Button(formulario, text="Criar", command=criar).pack(side="left")
        ttk.Button(corpo, text="Excluir selecionado", command=excluir).pack(anchor="e", pady=(10, 0))
        recarregar()

    def criar_pagina_revisoes(self):
        cabecalho = ttk.Frame(self.pagina_revisoes, padding=(18, 14))
        cabecalho.pack(fill="x")
        ttk.Button(cabecalho, text="‹", width=4,
                   command=lambda: self.mover_revisao(-1)).pack(side="left")
        self.label_data_revisao = ttk.Label(cabecalho, style="Titulo.TLabel")
        self.label_data_revisao.pack(side="left", padx=18)
        ttk.Button(cabecalho, text="Hoje", command=self.ir_para_hoje_revisao).pack(side="left")
        ttk.Button(cabecalho, text="›", width=4,
                   command=lambda: self.mover_revisao(1)).pack(side="left", padx=8)
        for texto in ("Semana", "Dia"):
            ttk.Radiobutton(cabecalho, text=texto, variable=self.visualizacao_revisao,
                            value=texto, command=self.atualizar_revisoes).pack(side="right", padx=6)

        self.area_revisoes = ttk.Frame(self.pagina_revisoes, padding=(18, 4))
        self.area_revisoes.pack(fill="both", expand=True)
        rodape = ttk.Frame(self.pagina_revisoes, padding=(18, 14))
        rodape.pack(fill="x")
        ttk.Button(rodape, text="+ Nova atividade", command=self.abrir_nova_revisao).pack(side="left")
        ttk.Label(rodape, text="Clique numa atividade para concluí-la • botão direito para excluir",
                  foreground="#666666").pack(side="left", padx=16)
        self.atualizar_revisoes()

    def atualizar_revisoes(self):
        for item in self.area_revisoes.winfo_children():
            item.destroy()
        if self.visualizacao_revisao.get() == "Dia":
            self.label_data_revisao.config(text=self.data_revisao.strftime("%d/%m/%Y"))
            self.mostrar_dia_revisao()
        else:
            inicio = self.data_revisao - timedelta(days=self.data_revisao.weekday())
            fim = inicio + timedelta(days=6)
            self.label_data_revisao.config(text=f"{inicio:%d/%m} – {fim:%d/%m/%Y}")
            self.mostrar_semana_revisao(inicio)

    def criar_area_rolavel_revisao(self):
        canvas = tk.Canvas(self.area_revisoes, bg=COR_PAINEL_SECUNDARIA, highlightthickness=1,
                           highlightbackground="#454545")
        barra = ttk.Scrollbar(self.area_revisoes, orient="vertical", command=canvas.yview)
        conteudo = ttk.Frame(canvas)
        conteudo.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        item = canvas.create_window((0, 0), window=conteudo, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(item, width=e.width))
        canvas.configure(yscrollcommand=barra.set)
        canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        return conteudo

    def mostrar_dia_revisao(self):
        conteudo = self.criar_area_rolavel_revisao()
        tarefas = [r for r in self.revisoes if r["data"] == self.data_revisao.isoformat()]
        ttk.Label(conteudo, text="Atividades para revisar", style="Cabecalho.TLabel").pack(
            anchor="w", padx=14, pady=(14, 8))
        if not tarefas:
            ttk.Label(conteudo, text="Nenhuma atividade para este dia.",
                      foreground="#777777").pack(anchor="w", padx=14, pady=12)
        for revisao in tarefas:
            self.criar_cartao_revisao(conteudo, revisao)

    def mostrar_semana_revisao(self, inicio):
        quadro = ttk.Frame(self.area_revisoes, relief="solid", borderwidth=1)
        quadro.pack(fill="both", expand=True)
        nomes = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for coluna in range(7):
            dia = inicio + timedelta(days=coluna)
            ttk.Label(quadro, text=f"{nomes[coluna]}\n{dia:%d/%m}", style="Cabecalho.TLabel",
                      anchor="center").grid(row=0, column=coluna, sticky="ew", padx=3, pady=8)
            lista = tk.Frame(quadro, bg=COR_PAINEL_SECUNDARIA, padx=5, pady=5)
            lista.grid(row=1, column=coluna, sticky="nsew", padx=2, pady=(0, 3))
            tarefas = sorted((r for r in self.revisoes if r["data"] == dia.isoformat()),
                             key=lambda r: r["titulo"].lower())
            if not tarefas:
                tk.Label(lista, text="Sem revisões", bg=COR_PAINEL_SECUNDARIA,
                         fg="#AAAAAA").pack(pady=12)
            for revisao in tarefas:
                self.criar_cartao_revisao(lista, revisao, compacto=True)
            quadro.columnconfigure(coluna, weight=1, uniform="dias")
        quadro.rowconfigure(1, weight=1)

    def criar_cartao_revisao(self, pai, revisao, compacto=False):
        texto = revisao["titulo"]
        cartao = tk.Label(pai, text=texto, bg=revisao["cor"], anchor="w", justify="left",
                          padx=8, pady=6, wraplength=115 if compacto else 700, cursor="hand2")
        cartao.pack(fill="x", padx=10 if not compacto else 0, pady=3)
        cartao.bind("<Button-1>", lambda _e, r=revisao: self.concluir_revisao(r))
        cartao.bind("<Button-3>", lambda _e, r=revisao: self.excluir_revisao(r))

    def mover_revisao(self, direcao):
        passo = 7 if self.visualizacao_revisao.get() == "Semana" else 1
        self.data_revisao += timedelta(days=direcao * passo)
        self.atualizar_revisoes()

    def ir_para_hoje_revisao(self):
        self.data_revisao = date.today()
        self.atualizar_revisoes()

    def abrir_nova_revisao(self):
        janela = tk.Toplevel(self.janela)
        janela.title("Nova atividade de revisão")
        janela.resizable(False, False)
        corpo = ttk.Frame(janela, padding=18)
        corpo.pack()
        ttk.Label(corpo, text="Atividade").grid(row=0, column=0, sticky="w", pady=6)
        titulo = ttk.Entry(corpo, width=32)
        titulo.grid(row=0, column=1, columnspan=2, padx=8, pady=6)
        titulo.focus_set()
        ttk.Label(corpo, text="Data inicial").grid(row=1, column=0, sticky="w", pady=6)
        campo_data = ttk.Entry(corpo, width=32)
        campo_data.insert(0, self.data_revisao.strftime("%d/%m/%Y"))
        campo_data.grid(row=1, column=1, columnspan=2, padx=8, pady=6)
        ttk.Label(corpo, text="Cor").grid(row=2, column=0, sticky="w", pady=6)
        cor = tk.StringVar(value="#FFD59E")

        def escolher_cor():
            escolhida = colorchooser.askcolor(cor.get(), parent=janela)[1]
            if escolhida:
                cor.set(escolhida)
                botao_cor.config(bg=escolhida)

        botao_cor = tk.Button(corpo, text="Escolher cor", bg=cor.get(), command=escolher_cor)
        botao_cor.grid(row=2, column=1, sticky="w", padx=8, pady=6)

        def adicionar():
            nome = titulo.get().strip()
            if not nome:
                messagebox.showwarning("Atividade", "Digite o nome da atividade.", parent=janela)
                return
            try:
                data_inicial = datetime.strptime(campo_data.get(), "%d/%m/%Y").date()
            except ValueError:
                messagebox.showerror("Data inválida", "Use o formato DD/MM/AAAA.", parent=janela)
                return
            primeira_revisao = data_inicial + timedelta(days=1)
            self.revisoes.append({"titulo": nome, "cor": cor.get(),
                                  "data": primeira_revisao.isoformat(), "etapa": 0})
            self.data_revisao = primeira_revisao
            self.salvar_dados()
            janela.destroy()
            self.atualizar_revisoes()

        ttk.Label(corpo, text="A primeira revisão será marcada para o dia seguinte.",
                  foreground="#666").grid(row=3, column=0, columnspan=3, pady=(8, 2))
        ttk.Button(corpo, text="Adicionar", command=adicionar).grid(row=4, column=2, sticky="e", pady=(12, 0))

    def concluir_revisao(self, revisao):
        opcoes = ((2, 4), (4, 7), (7, 14), (14,))[min(revisao.get("etapa", 0), 3)]
        janela = tk.Toplevel(self.janela)
        janela.title("Concluir revisão")
        janela.resizable(False, False)
        corpo = ttk.Frame(janela, padding=20)
        corpo.pack()
        ttk.Label(corpo, text=f'Quando revisar "{revisao["titulo"]}" novamente?',
                  style="Cabecalho.TLabel").pack(pady=(0, 14))

        def agendar(dias):
            data_anterior = date.fromisoformat(revisao["data"])
            revisao["data"] = (data_anterior + timedelta(days=dias)).isoformat()
            revisao["etapa"] = min(revisao.get("etapa", 0) + 1, 3)
            self.salvar_dados()
            janela.destroy()
            self.atualizar_revisoes()

        botoes = ttk.Frame(corpo)
        botoes.pack()
        for dias in opcoes:
            ttk.Button(botoes, text=f"Em {dias} dias", command=lambda d=dias: agendar(d)).pack(
                side="left", padx=6)

    def excluir_revisao(self, revisao):
        if messagebox.askyesno("Excluir atividade", f'Excluir "{revisao["titulo"]}" da repetição espaçada?'):
            self.revisoes.remove(revisao)
            self.salvar_dados()
            self.atualizar_revisoes()

    def excluir_tarefa(self, tarefa):
        if messagebox.askyesno("Excluir tarefa", f'Excluir "{tarefa["titulo"]}"?'):
            self.tarefas.remove(tarefa)
            self.salvar_dados()
            self.atualizar_agenda()


def main():
    janela = tk.Tk()
    AgendaApp(janela)
    janela.mainloop()


if __name__ == "__main__":
    main()
