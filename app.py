from flask import Flask, render_template, request, redirect, url_for, flash
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import utils.db as db
import utils.auth as auth
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "chave_super_segura_kajiombo")

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


@app.route("/exportar/alunos/<formato>")
def exportar_alunos(formato):
    # Captura filtros da query string
    classe = request.args.get("classe")
    status = request.args.get("status")

    # Busca alunos com filtros aplicados
    alunos = db.listar_alunos_filtrados(classe=classe, status=status)

    if formato == "csv":
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(["ID", "Nome", "Classe", "Encarregado", "Status"])
        for a in alunos:
            writer.writerow([a["id_aluno"], a["nome"], a["classe"], a["encarregado"], a["status"]])
        output = si.getvalue()
        return Response(output, mimetype="text/csv",
                        headers={"Content-Disposition":"attachment;filename=alunos.csv"})

    elif formato == "xls":
        si = StringIO()
        writer = csv.writer(si, delimiter="\t")
        writer.writerow(["ID", "Nome", "Classe", "Encarregado", "Status"])
        for a in alunos:
            writer.writerow([a["id_aluno"], a["nome"], a["classe"], a["encarregado"], a["status"]])
        output = si.getvalue()
        return Response(output, mimetype="application/vnd.ms-excel",
                        headers={"Content-Disposition":"attachment;filename=alunos.xls"})

    else:
        return "Formato não suportado", 400

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
def cadastrar_adesao():   # ← nome da função agora bate com o template
    if request.method == "POST":
        tipo = request.form.get("tipo")
        try:
            valor = float(request.form.get("valor", 0))
        except ValueError:
            flash("Valor inválido!", "danger")
            return redirect(url_for("cadastrar_adesao"))

        db.cadastrar_tipo_adesao(tipo, valor)
        flash("Tipo de adesão cadastrado com sucesso!", "success")
        return redirect(url_for("dashboard"))

    adesoes = db.listar_tipos_adesao()
    return render_template("cadastrar_tipo_adesao.html", adesoes=adesoes)

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
        classe = request.form.get("classe")
        status = request.form.get("status")
        rota_antiga = aluno['rota']
        if rota_nova != rota_antiga:
            mensagem = f"⚠️ Aluno {nome} mudou da rota {rota_antiga} para {rota_nova}"
            db.registrar_notificacao(mensagem, tipo="alerta")
        db.atualizar_aluno(id_aluno, nome, encarregado, telefone, rota_nova, periodo, classe, status)
        return redirect(url_for("dashboard"))
    return render_template("editar_aluno.html", aluno=aluno, rotas=rotas)



@app.route("/pesquisar_alunos")
def pesquisar_alunos():
    termo = request.args.get("q", "")
    conn = sqlite3.connect("frota.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome, classe, periodo, encarregado, telefone, rota, adesao, status_ativo
        FROM relatorio_alunos
        WHERE nome LIKE ?
        LIMIT 10
    """, (f"{termo}%",))
    rows = cursor.fetchall()
    conn.close()

    alunos = []
    for r in rows:
        alunos.append({
            "id": r[0],
            "nome": r[1],
            "classe": r[2],
            "periodo": r[3],
            "encarregado": r[4],
            "telefone": r[5],
            "rota": r[6],
            "adesao": r[7],
            "status": r[8]
        })
    return jsonify(alunos)

@app.route("/buscar_alunos")
def buscar_alunos_route():
    termo = request.args.get("query", "").strip()
    alunos = db.buscar_alunos_autocomplete(termo)
    return jsonify(alunos)


    # GET → mostra formulário + lista atual
    adesoes = listar_tipos_adesao()
    return render_template("cadastrar_tipo_adesao.html", adesoes=adesoes)

@app.route("/listar_adesoes")
def listar_adesoes_route():
    dados = listar_tipos_adesao()
    return jsonify([dict(row) for row in dados])

@app.route("/novo_contrato", methods=["POST"])
def novo_contrato():
    aluno_id = request.form.get("id_aluno")
    tipo_contrato = request.form.get("tipo_contrato")   # Adesão, Confirmação, Taxa Reativação
    valor_total = float(request.form.get("valor_total"))
    valor_pago = float(request.form.get("valor_pago"))
    metodo = request.form.get("metodo")
    data_pagamento = request.form.get("data_pagamento")

    conn = sqlite3.connect("frota.db")
    cursor = conn.cursor()

    # Verifica se aluno já está ativo
    cursor.execute("SELECT status FROM alunos WHERE id_aluno = ?", (aluno_id,))
    row = cursor.fetchone()
    if row and row[0] == "Ativo":
        conn.close()
        return "Aluno já possui contrato ativo. Não é possível criar novo contrato."

    # Atualiza aluno
    cursor.execute("""
        UPDATE alunos
        SET status = 'Ativo',
            adesao = ?,
            data_adesao = ?
        WHERE id_aluno = ?
    """, (tipo_contrato, data_pagamento, aluno_id))

    # Calcula remanescente
    remanescente = valor_total - valor_pago

    # Gera número de fatura (exemplo simples)
    numero_fatura = f"FAT-{aluno_id}-{int(datetime.now().timestamp())}"

    # Buscar rota do aluno (já definida na inscrição)
    cursor.execute("SELECT id_rota FROM alunos WHERE id_aluno = ?", (aluno_id,))
    row_rota = cursor.fetchone()
    id_rota = row_rota[0] if row_rota else None

    # Insere fatura
    cursor.execute("""
        INSERT INTO faturas (
            numero_fatura, id_aluno, id_rota, tipo, mes, valor,
            valor_pago, remanescente, metodo, data_pagamento,
            observacoes, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        numero_fatura, aluno_id, id_rota,
        "Contrato",          # tipo = descrição contrato
        tipo_contrato,       # mes = tipo de contrato selecionado
        valor_total,
        valor_pago,
        remanescente,
        metodo,
        data_pagamento,
        None,                # observações (pode ser preenchido se quiser)
        "Emitida"
    ))

    conn.commit()
    conn.close()

    return redirect(url_for("fatura_recibo", aluno_id=aluno_id))

@app.route("/buscar_adesao")
def buscar_adesao_route():
    tipo = request.args.get("tipo", "").strip()
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT valor FROM tipos_adesao WHERE tipo = ?", (tipo,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({"valor": row["valor"]})
    else:
        return jsonify({"valor": None})

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

# -------------------------------

@app.route("/faturas")
def faturas():
    lista = listar_faturas()
    return render_template("relatorio_faturas.html", faturas=lista)



@app.route("/emitir_fatura", methods=["GET", "POST"])
def emitir_fatura():
    if request.method == "POST":
        # Captura dos dados do formulário
        id_aluno = request.form.get("id_aluno")
        id_rota = request.form.get("id_rota")
        tipo = request.form.get("tipo")
        meses_selecionados = request.form.getlist("quantidade_meses")
        mes = request.form.get("mes") or (meses_selecionados[0] if meses_selecionados else None)

        try:
           valor_pago = float(request.form.get("valor_pago", 0))
        except ValueError:
            return render_template("emitir_fatura.html", erro="Valor pago inválido")

        metodo = request.form.get("metodo")
        data_pagamento = request.form.get("data_pagamento")
        observacoes = request.form.get("observacoes")

        # Verificar se aluno foi selecionado
        if not id_aluno:
            return render_template("emitir_fatura.html", erro="Selecione um aluno.")

        aluno = db.obter_aluno(id_aluno)

        # Bloqueios de status
        if tipo == "mensalidade" and aluno["status"] != "Ativo":
            return render_template(
                "emitir_fatura.html",
                erro="Aluno ainda não está ativo. Pague adesão/confirmacao/reativacao primeiro.",
                aluno=aluno
            )

        if tipo in ["adesao", "confirmacao", "reativacao"] and aluno["status"] == "Ativo":
            return render_template(
                "emitir_fatura.html",
                erro="Aluno já está ativo. Não pode pagar adesão/confirmacao/reativacao.",
                aluno=aluno
            )

        # Buscar preço da rota
        valor_rota = db.valor_rota(id_rota)
        if valor_rota is None:
            return render_template("emitir_fatura.html", erro="Rota inválida ou não encontrada.")

        # Cálculos principais
        quantidade_meses = len(meses_selecionados) if tipo == "mensalidade" else 1
        subtotal = valor_rota * quantidade_meses
        total_pagar = subtotal
        total_recebido = valor_pago
        saldo_usado = min(total_recebido, total_pagar)
        saldo_remanescente = max(0, total_recebido - total_pagar)

        # Construção da lista de serviços
        servicos = []
        if tipo in ["adesao", "confirmacao", "reativacao"]:
            servicos.append({
                "descricao": f"Taxa de {tipo.capitalize()}",
                "preco_unitario": valor_rota,
                "quantidade": 1
            })
        elif tipo == "mensalidade":
            for mes_item in meses_selecionados:
                servicos.append({
                    "descricao": f"Mensalidade - {mes_item}",
                    "preco_unitario": valor_rota,
                    "quantidade": 1
                })

        # Inserir fatura no banco
        db.inserir_fatura(
            tipo=tipo,
            mes=mes,
            valor=subtotal,
            valor_pago=valor_pago,
            remanescente=saldo_remanescente,
            metodo=metodo,
            data_pagamento=data_pagamento,
            id_aluno=id_aluno,
            id_rota=id_rota,
            observacoes=observacoes
        )

        # Atualizar status do aluno se adesão/confirmacao/reativacao
        if tipo in ["adesao", "confirmacao", "reativacao"]:
            db.atualizar_status_aluno(id_aluno, "Ativo")

        # Buscar última fatura emitida
        fatura = db.obter_ultima_fatura(id_aluno)

        # Garantir que o objeto fatura tem todos os campos necessários
        fatura.update({
            "subtotal": subtotal,
            "total_pagar": total_pagar,
            "total_recebido": total_recebido,
            "saldo_usado": saldo_usado,
            "saldo_remanescente": saldo_remanescente,
            "servicos": servicos,
            "emitido_por": "Sistema LUINDOPLUS",
            "data_pagamento": data_pagamento
        })

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
    faturas = db.listar_faturas()  # usa a função que já tens
    return render_template("relatorio_faturas.html", faturas=faturas)


@app.route("/fatura_recibo/<int:aluno_id>")
def fatura_recibo(aluno_id):
    conn = sqlite3.connect("frota.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Consulta ajustada para montar a descrição corretamente
    cursor.execute("""
        SELECT
            f.id_fatura,
            f.numero_fatura,
            CASE
                WHEN f.tipo IN ('Adesão','Confirmação','Taxa de Reativação')
                THEN 'Contrato - ' || f.tipo
                WHEN f.tipo = 'Mensalidade'
                THEN 'Mensalidade - ' || f.mes
                ELSE f.tipo
            END AS descricao_contrato,
            f.valor,
            f.valor_pago,
            f.remanescente,
            f.metodo,
            f.data_pagamento,
            f.status,
            a.nome AS nome_aluno,
            a.classe,
            a.encarregado
        FROM faturas f
        JOIN alunos a ON f.id_aluno = a.id_aluno
        WHERE f.id_aluno = ?
        ORDER BY f.id_fatura DESC
        LIMIT 1
    """, (aluno_id,))
    fatura = cursor.fetchone()
    conn.close()

    if not fatura:
        return "Nenhuma fatura encontrada para este aluno."

    return render_template("fatura_recibo.html", fatura=dict(fatura))

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
    import os
    port = int(os.getenv("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
