


from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import utils.db as db
import utils.auth as auth

app = Flask(__name__)
app.secret_key = "chave_super_segura_kajiombo"

# ============================
# 🔒 Função de verificação de permissões
# ============================
def verificar_permissao(perfis_permitidos):
    if "usuario" not in session or session.get("perfil") not in perfis_permitidos:
        return False
    return True

# ============================
# 🔑 Login / Logout
# ============================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        perfil = auth.validar_login(usuario, senha)  # retorna perfil se login válido
        if perfil:
            session["usuario"] = usuario
            session["perfil"] = perfil
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", erro="Usuário ou senha inválidos")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ============================
# 👥 Gestão de Usuários
# ============================
@app.route("/usuarios")
def listar_usuarios():
    if not verificar_permissao(["Administrador"]):
        return redirect(url_for("dashboard"))
    usuarios = auth.listar_usuarios()
    return render_template("listar_usuarios.html", usuarios=usuarios)

@app.route("/remover_usuario/<usuario>")
def remover_usuario(usuario):
    if not verificar_permissao(["Administrador"]):
        return redirect(url_for("dashboard"))
    auth.remover_usuario(usuario)
    return redirect(url_for("listar_usuarios"))

@app.route("/resetar_senha/<usuario>", methods=["GET", "POST"])
def resetar_senha(usuario):
    if not verificar_permissao(["Administrador"]):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        senha_nova = request.form.get("senha")
        sucesso, msg = auth.resetar_senha(usuario, senha_nova)
        if sucesso:
            return render_template("resetar_senha.html", usuario=usuario, sucesso=msg)
        else:
            return render_template("resetar_senha.html", usuario=usuario, erro=msg)

    return render_template("resetar_senha.html", usuario=usuario)

# ============================
# 📊 Dashboard
# ============================
@app.route("/")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))
    resumo = db.obter_resumo()
    periodo = db.obter_periodo_atual()
    alunos = db.listar_alunos()
    return render_template("dashboard.html", resumo=resumo, periodo=periodo, alunos=alunos)


# ============================
# 👨‍🎓 Rotas Alunos
# ============================
@app.route("/cadastro/aluno", methods=["GET", "POST"])
def cadastro_aluno():
    # ✅ Verificação de permissão
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        # Captura os dados do formulário
        nome = request.form["nome"]
        classe = request.form["classe"]
        encarregado = request.form["encarregado"]
        id_rota = request.form["id_rota"]   # chave estrangeira da rota
        valor = request.form["valor_rota"]  # ✅ captura o preço da rota
        periodo = request.form["periodo"]
        telefone = request.form["telefone"]
        status = "Inativo"

        # Salva no banco
        db.cadastrar_aluno(nome, classe, encarregado, id_rota, valor, periodo, telefone, status)

        flash("Aluno cadastrado com sucesso!", "success")
        return redirect(url_for("relatorio_alunos"))

    # Carrega rotas para o select do formulário
    rotas = db.listar_rotas()
    return render_template("cadastro_aluno.html", rotas=rotas)


@app.route("/relatorio/alunos")


@app.route("/relatorio/alunos")
def relatorio_alunos():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("login"))

    # chama a função do db.py
    alunos = db.listar_alunos()
    return render_template("relatorio_alunos.html", alunos=alunos)


# Exemplo de rota para relatório de devedores
@app.route("/relatorio/devedores")
def relatorio_devedores():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("login"))

    devedores = db.listar_devedores()
    return render_template("relatorio_devedores.html", alunos=devedores)
@app.route("/notificacoes")
def notificacoes():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("login"))

    lista = db.listar_notificacoes()
    return render_template("notificacoes.html", notificacoes=lista)

@app.route("/inativar/aluno/<int:id_aluno>")
def inativar_aluno(id_aluno):
    if not verificar_permissao(["Administrador"]):
        return redirect(url_for("relatorio_alunos"))
    db.inativar_aluno(id_aluno)
    return redirect(url_for("relatorio_alunos"))


@app.route("/cadastrar_tipo_adesao", methods=["GET", "POST"])
def cadastrar_tipo_adesao_route():
    if request.method == "POST":
        tipo = request.form["tipo"]
        valor = float(request.form["valor"])
        db.cadastrar_tipo_adesao(tipo, valor)   # ✅ chama função do db.py
        flash("Tipo de adesão cadastrado com sucesso!", "success")
        return redirect(url_for("dashboard"))

    return render_template("cadastrar_tipo_adesao.html")
@app.route("/autocomplete_aluno")
def autocomplete_aluno():
    termo = request.args.get("q", "").strip()
    resultados = db.buscar_alunos_relatorio(termo)

    alunos = []
    for row in resultados:
        alunos.append({
            "id_aluno": row["id_aluno"],
            "nome": row["nome"],
            "classe": row["classe"],
            "periodo": row["periodo"],
            "encarregado": row["encarregado"],
            "rota": row["rota"],
            "ultimo_mes": row["ultimo_mes"]
        })
    return jsonify(alunos)
# ============================
# 🛣️ Rotas Rotas
# ============================
@app.route("/cadastro/rota", methods=["GET", "POST"])
def cadastro_rota():
    if not verificar_permissao(["Administrador"]):
        return redirect(url_for("relatorio_rotas"))

    if request.method == "POST":
        db.cadastrar_rota(
            request.form["nome"],
            request.form["preco"]
        )
        return redirect(url_for("relatorio_rotas"))
    return render_template("cadastro_rota.html")

@app.route("/relatorio/rotas")
def relatorio_rotas():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("login"))
    rotas = db.listar_rotas()
    return render_template("relatorio_rotas.html", dados=rotas)



@app.route("/editar/aluno/<int:id_aluno>", methods=["GET", "POST"])
def editar_aluno(id_aluno):
    aluno = db.buscar_aluno(id_aluno)
    rotas = db.relatorio_rotas()
    if request.method == "POST":
        nome = request.form.get("nome")
        encarregado = request.form.get("encarregado")
        telefone = request.form.get("telefone")
        rota_nova = int(request.form.get("rota"))
        periodo = request.form.get("periodo")
        classe = request.form.get("classe")
        status = request.form.get("status")
        rota_antiga = aluno['rota']
        if rota_nova != rota_antiga:
            mensagem = f"⚠️ Aluno {nome} mudou da rota {rota_antiga} para {rota_nova}"
            db.registrar_notificacao(mensagem, tipo="alerta")
        db.atualizar_aluno(id_aluno, nome, encarregado, telefone, rota_nova, periodo, classe, status)
        return redirect(url_for("dashboard"))
    return render_template("editar_aluno.html", aluno=aluno, rotas=rotas)

@app.route("/buscar_alunos")
def buscar_alunos_route():
    termo = request.args.get("query", "").strip()
    alunos = db.buscar_alunos_autocomplete(termo)
    return jsonify(alunos)

# 🔎 API de alunos (autocomplete)
@app.route("/api/alunos")
def api_alunos():
    termo = request.args.get("query", "").strip()
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_aluno, id_rota, nome, classe, encarregado, rota, ultimo_mes
        FROM alunos
        WHERE nome LIKE ? OR classe LIKE ? OR id LIKE ?
        LIMIT 10
    """, (f"%{termo}%", f"%{termo}%", f"%{termo}%"))

    resultados = cursor.fetchall()
    conn.close()

    alunos = []
    for r in resultados:
        alunos.append({
            "id_aluno": r[0],
            "nome": r[1],
            "classe": r[2],
            "encarregado": r[3],
            "rota": r[4],
            "ultimo_mes": r[5]
        })

    return jsonify(alunos)


# 🚍 API de rotas (preço da rota)
@app.route("/api/rotas")
def api_rotas():
    rota_nome = request.args.get("rota", "").strip()
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_rota, nome, preco
        FROM rotas
        WHERE nome LIKE ?
        LIMIT 5
    """, (f"%{rota_nome}%",))

    resultados = cursor.fetchall()
    conn.close()

    rotas = []
    for r in resultados:
        rotas.append({
            "id_rota": r[0],
            "nome": r[1],
            "preco": r[2]
        })

    return jsonify(rotas)
# ============================
# 🚐 Motoristas
# ============================
@app.route("/cadastro/motorista", methods=["GET", "POST"])
def cadastro_motorista():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        db.cadastrar_motorista(request.form["nome"], request.form["telefone"], request.form["carta"])
        return redirect(url_for("relatorio_motoristas"))
    return render_template("cadastro_motorista.html")

@app.route("/relatorio/motoristas")
def relatorio_motoristas():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("dashboard"))
    motoristas = db.relatorio_motoristas()
    return render_template("relatorio_motoristas.html", motoristas=motoristas)

# ============================
# 🚍 Viaturas
# ============================
@app.route("/cadastro/viatura", methods=["GET", "POST"])
def cadastro_viatura():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        db.cadastrar_viatura(request.form["matricula"], request.form["modelo"], request.form["capacidade"])
        return redirect(url_for("relatorio_viaturas"))
    return render_template("cadastro_viatura.html")

@app.route("/relatorio/viaturas")
def relatorio_viaturas():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("dashboard"))
    viaturas = db.relatorio_viaturas()
    return render_template("relatorio_viaturas.html", viaturas=viaturas)


# ============================
# 💳 Faturação (Tesouraria)
# ============================
def listar_faturas():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            f.id_fatura,
            f.numero_fatura,
            f.tipo,
            f.mes,
            f.descricao,
            f.valor,
            f.valor_pago,
            f.remanescente,
            f.metodo,
            f.data_pagamento,
            f.status,
            a.id_aluno,
            a.nome AS nome_aluno,
            a.classe,
            a.encarregado
        FROM faturas f
        JOIN alunos a ON f.id_aluno = a.id_aluno
        ORDER BY f.id_fatura DESC
    """)
    resultados = cursor.fetchall()
    conn.close()
    return [dict(row) for row in resultados]

# -------------------------------
def get_fatura(id_fatura):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            f.id_fatura,
            f.numero_fatura,
            f.tipo,
            f.mes,
            f.descricao,
            f.valor,
            f.valor_pago,
            f.remanescente,
            f.metodo,
            f.data_pagamento,
            f.status,
            a.id_aluno,
            a.nome AS nome_aluno,
            a.classe,
            a.encarregado,
            f.utilizador
        FROM faturas f
        JOIN alunos a ON f.id_aluno = a.id_aluno
        WHERE f.id_fatura = ?
    """, (id_fatura,))
    resultado = cursor.fetchone()
    conn.close()
    return dict(resultado) if resultado else None

# -------------------------------
@app.route("/faturas")
def faturas():
    lista = listar_faturas()
    return render_template("relatorio_faturas.html", faturas=lista)


@app.route("/emitir_fatura", methods=["GET", "POST"])
def emitir_fatura():
    if request.method == "POST":
        id_aluno = request.form.get("id_aluno")
        id_rota = request.form.get("id_rota")
        tipo = request.form.get("tipo")
        mes = request.form.get("mes")

        # Verificar se aluno foi selecionado
        if not id_aluno:
            return render_template(
                "emitir_fatura.html",
                erro="É obrigatório selecionar um aluno antes de emitir a fatura."
            )

        aluno = db.obter_aluno(id_aluno)

        # Bloqueia mensalidade se aluno não ativo
        if tipo == "mensalidade" and aluno["status"] != "Ativo":
            return render_template(
                "emitir_fatura.html",
                erro="Aluno ainda não está ativo. Pague adesão/confirmacao/reativacao primeiro.",
                aluno=aluno
            )

        # Bloqueia adesão/confirmacao/reativacao se aluno já ativo
        if tipo in ["adesao", "confirmacao", "reativacao"] and aluno["status"] == "Ativo":
            return render_template(
                "emitir_fatura.html",
                erro="Aluno já está ativo. Não pode pagar adesão/confirmacao/reativacao novamente.",
                aluno=aluno
            )

        # Buscar preço da rota com proteção contra None
        valor = db.valor_rota(id_rota)
        if valor is None:
            return render_template(
                "emitir_fatura.html",
                erro="Rota não encontrada. Verifique os dados do aluno."
            )

        # Se for mensalidade de vários meses
        meses = int(request.form.get("quantidade_meses", 1))
        valor_total = valor * meses

        valor_pago = float(request.form.get("valor_pago"))
        remanescente = valor_total - valor_pago

        metodo = request.form.get("metodo")
        data_pagamento = request.form.get("data_pagamento")
        observacoes = request.form.get("observacoes")

        # Inserir fatura
        db.inserir_fatura(
            tipo=tipo,
            mes=mes,
            valor=valor_total,
            valor_pago=valor_pago,
            remanescente=remanescente,
            metodo=metodo,
            data_pagamento=data_pagamento,
            id_aluno=id_aluno,
            id_rota=id_rota,
            observacoes=observacoes
        )

        # Atualizar status do aluno se adesão/confirmacao/reativacao
        if tipo in ["adesao", "confirmacao", "reativacao"] and aluno["status"] != "Ativo":
            db.atualizar_status_aluno(id_aluno, "Ativo")

        # Buscar última fatura emitida
        fatura = db.obter_ultima_fatura(id_aluno)
        return render_template("fatura_recibo.html", fatura=fatura)

    # GET → mostra formulário
    return render_template("emitir_fatura.html")

@app.route("/editar_fatura/<int:id_fatura>", methods=["GET", "POST"])
def editar_fatura(id_fatura):
    fatura = db.obter_fatura(id_fatura)
    alunos = db.listar_alunos()
    if request.method == "POST":
        aluno = request.form.get("aluno")
        valor = request.form.get("valor")
        metodo = request.form.get("metodo")
        data_pagamento = request.form.get("data_pagamento")
        observacoes = request.form.get("observacoes")
        db.atualizar_fatura(id_fatura, aluno, valor, metodo, data_pagamento, observacoes)
        return redirect(url_for("imprimir_fatura", id_fatura=id_fatura))
    return render_template("editar_fatura.html", fatura=fatura, alunos=alunos)


@app.route("/imprimir_fatura/<int:id_fatura>")
def imprimir_fatura(id_fatura):
    fatura = db.obter_fatura(id_fatura)
    aluno = db.obter_aluno(fatura['id_aluno'])
    return render_template("fatura_recibo.html", fatura=fatura, aluno=aluno)


@app.route("/relatorio/faturas")
def relatorio_faturas():
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("dashboard"))
    faturas = db.relatorio_faturas()
    return render_template("relatorio_faturas.html", faturas=faturas)
# ============================
# 📑 Relatórios Financeiros
# ============================
@app.route("/relatorio/financeiro/<ano>")
def relatorio_financeiro(ano):
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("dashboard"))
    dados = db.relatorio_financeiro_bi_anual(ano)
    return render_template("relatorio_financeiro.html", dados=dados, ano=ano)

@app.route("/relatorio/contabilistico/<ano>")
def relatorio_contabilistico(ano):
    if not verificar_permissao(["Administrador", "Operador"]):
        return redirect(url_for("dashboard"))


# ============================
# 🚀 Inicialização
# ============================
if __name__ == "__main__":
    db.create_tables()
    auth.create_user_table()
    auth.seed_usuarios_iniciais()  # cria usuários iniciais
    app.run(debug=True)
