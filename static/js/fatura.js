// Autocomplete de alunos
document.getElementById("pesquisaAluno").addEventListener("input", async function () {
    let termo = this.value.trim();
    let sugestoes = document.getElementById("sugestoes");

    if (termo.length < 2) {
        sugestoes.innerHTML = "";
        return;
    }

    try {
        let response = await fetch(`/buscar_alunos?query=${encodeURIComponent(termo)}`);
        let alunos = await response.json();

        sugestoes.innerHTML = "";
        alunos.forEach(aluno => {
            let li = document.createElement("li");
            li.classList.add("list-group-item");
            li.textContent = `${aluno.id} - ${aluno.nome}`;

            li.onclick = function () {
                // Preenche campos ocultos obrigatórios
                document.getElementById("id_aluno").value = aluno.id;
                document.getElementById("id_rota").value = aluno.id_rota;

                // Preenche campos visíveis
                document.getElementById("nome_aluno").value = aluno.nome;
                document.getElementById("classe_aluno").value = aluno.classe;
                document.getElementById("periodo_aluno").value = aluno.periodo;
                document.getElementById("encarregado_aluno").value = aluno.encarregado;
                document.getElementById("telefone_aluno").value = aluno.telefone;
                document.getElementById("status_aluno").value = aluno.status;
                document.getElementById("ultimo_mes_pago").value = aluno.ultimo_mes_pago || "Sem pagamento";
                document.getElementById("rota_aluno").value = aluno.nome_rota;
                document.getElementById("valor_rota").value = aluno.valor_rota;

                // Limpa lista e coloca o nome no campo de busca
                sugestoes.innerHTML = "";
                document.getElementById("pesquisaAluno").value = aluno.nome;

                // Bloqueia meses já pagos
                bloquearMesesPagos(aluno.ultimo_mes_pago);

                // Atualiza visibilidade conforme status
                atualizarCamposPorStatus(aluno.status);
            };

            sugestoes.appendChild(li);
        });
    } catch (error) {
        console.error("Erro ao buscar alunos:", error);
    }
});

// Função para controlar visibilidade e lógica do formulário
function atualizarCamposPorStatus(status) {
    const tipoSelect = document.getElementById("tipo");
    const tipoFaturaDiv = document.getElementById("tipo_fatura");
    const valorRotaDiv = document.getElementById("valor_rota_div");
    const mesesContainer = document.getElementById("meses-container");

    if (status === "Ativo") {
        tipoFaturaDiv.style.display = "none";
        valorRotaDiv.style.display = "block";
        tipoSelect.value = "Mensalidade";
        mesesContainer.style.display = "block";
    } else if (status === "Inativo") {
        tipoFaturaDiv.style.display = "block";
        valorRotaDiv.style.display = "block";
        mesesContainer.style.display = "none";
    } else {
        tipoFaturaDiv.style.display = "block";
        valorRotaDiv.style.display = "block";
        mesesContainer.style.display = "block";
    }
}

// Bloqueia meses já pagos
function bloquearMesesPagos(ultimoMesPago) {
    const mesesSelect = document.getElementById("meses");
    if (!mesesSelect) return;

    const meses = ["Setembro","Outubro","Novembro","Dezembro","Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho"];
    const indexUltimo = meses.indexOf(ultimoMesPago);

    if (indexUltimo >= 0) {
        Array.from(mesesSelect.options).forEach((opt, idx) => {
            opt.disabled = idx <= indexUltimo;
        });
    }
}

// Listener para cálculo de mensalidade (Ativo)
document.getElementById("meses").addEventListener("change", function(event) {
    const selecionados = Array.from(event.target.selectedOptions).map(opt => opt.index);
    selecionados.sort((a, b) => a - b);

    const valorRota = parseFloat(document.getElementById("valor_rota").value || 0);

    // Verifica se os meses selecionados são consecutivos
    let consecutivos = true;
    for (let i = 1; i < selecionados.length; i++) {
        if (selecionados[i] !== selecionados[i - 1] + 1) {
            consecutivos = false;
            break;
        }
    }

    if (!consecutivos) {
        alert("⚠️ Deve selecionar meses consecutivos sem saltar.");
        event.target.selectedIndex = -1;
        document.getElementById("valor_total").value = "";
        document.getElementById("remanescente").value = "";
        return;
    }

    const total = valorRota * selecionados.length;
    document.getElementById("valor_total").value = total;

    const valorPago = parseFloat(document.getElementById("valor_pago").value || 0);
    document.getElementById("remanescente").value = total - valorPago;
});

// Listener para tipo de fatura (Inativo)
document.getElementById("tipo").addEventListener("change", async function(event) {
    const tipoSelecionado = event.target.value;

    if (["Adesão", "Confirmação", "Taxa de Reativação"].includes(tipoSelecionado)) {
        try {
            let resp = await fetch(`/buscar_adesao?tipo=${encodeURIComponent(tipoSelecionado)}`);
            let dados = await resp.json();

            if (dados && dados.valor) {
                document.getElementById("preco_unit").value = dados.valor;
                document.getElementById("valor_total").value = dados.valor;

                const valorPago = parseFloat(document.getElementById("valor_pago").value || 0);
                document.getElementById("remanescente").value = dados.valor - valorPago;
            } else {
                document.getElementById("preco_unit").value = "";
                document.getElementById("valor_total").value = "";
                document.getElementById("remanescente").value = "";
            }
        } catch (err) {
            console.error("Erro ao buscar valor de adesão:", err);
        }
    }
});

// Executa ao carregar a página
window.addEventListener("DOMContentLoaded", function () {
    const status = document.getElementById("status_aluno").value;
    atualizarCamposPorStatus(status);
});
