$(document).ready(function() {
  var table = $('#alunosTable').DataTable({
    paging: true,
    searching: true,
    ordering: true,
    pageLength: 20,
    lengthMenu: [10, 20, 50, 100],
    dom: 'Bfrtip',
    buttons: [
      {
        extend: 'csvHtml5',
        text: '⬇️ Exportar CSV',
        className: 'btn btn-success btn-sm',
        exportOptions: { columns: ':visible' }
      },
      {
        extend: 'excelHtml5',
        text: '⬇️ Exportar Excel',
        className: 'btn btn-info btn-sm',
        exportOptions: { columns: ':visible' }
      },
      {
        extend: 'print',
        text: '🖨️ Imprimir',
        className: 'btn btn-secondary btn-sm',
        exportOptions: { columns: ':visible' }
      }
    ],
    language: {
      url: "https://cdn.datatables.net/plug-ins/1.13.6/i18n/pt-PT.json"
    },
    fixedColumns: {
      leftColumns: 2 // fixa ID e Nome
    }
  });

  // Filtros múltiplos por coluna (inputs e selects)
  $('#alunosTable thead tr:eq(1) th').each(function(i) {
    var input = $('input, select', this);
    input.on('keyup change', function() {
      table.column(i).search($(this).val(), true, false).draw();
    });
  });
});


document.addEventListener("DOMContentLoaded", function() {
    const pesquisa = document.getElementById("pesquisaAluno");
    const sugestoes = document.getElementById("sugestoes");

    pesquisa.addEventListener("input", async function() {
        let termo = pesquisa.value;
        if (termo.length < 2) {
            sugestoes.innerHTML = "";
            return;
        }

        try {
            // Podes trocar para /pesquisar_alunos se mudares no Flask
            let resp = await fetch(`/buscar_alunos?q=${encodeURIComponent(termo)}`);
            let alunos = await resp.json();

            sugestoes.innerHTML = "";
            alunos.forEach(aluno => {
                let li = document.createElement("li");
                li.classList.add("list-group-item");
                li.textContent = `${aluno.nome} (${aluno.status})`;

                li.addEventListener("click", function() {
                    // Bloqueia se já estiver ativo
                    if (aluno.status === "Ativo") {
                        alert("⚠️ Este aluno já possui contrato ativo. Não é permitido novo contrato.");
                        sugestoes.innerHTML = "";
                        pesquisa.value = "";
                        return;
                    }

                    // Preenche campos ocultos
                    document.getElementById("id_aluno").value = aluno.id;
                    document.getElementById("id_rota").value = aluno.rota;

                    // Preenche campos visíveis
                    document.getElementById("nome_aluno").value = aluno.nome;
                    document.getElementById("classe_aluno").value = aluno.classe;
                    document.getElementById("periodo_aluno").value = aluno.periodo;
                    document.getElementById("encarregado_aluno").value = aluno.encarregado;
                    document.getElementById("telefone_aluno").value = aluno.telefone;
                    document.getElementById("rota_aluno").value = aluno.rota;
                    document.getElementById("adesao_aluno").value = aluno.adesao || "Sem adesão";
                    document.getElementById("status_aluno").value = aluno.status;

                    sugestoes.innerHTML = "";
                    pesquisa.value = aluno.nome;
                });

                sugestoes.appendChild(li);
            });
        } catch (err) {
            console.error("Erro ao buscar alunos:", err);
        }
    });
});

// Atualiza o valor total quando o contrato é selecionado
function atualizarValor() {
    const contrato = document.getElementById("contrato");
    const valorTotalCampo = document.getElementById("valor_total");

    // Pega o atributo data-valor da opção selecionada
    const selectedOption = contrato.options[contrato.selectedIndex];
    const valorContrato = selectedOption && selectedOption.getAttribute("data-valor")
        ? parseFloat(selectedOption.getAttribute("data-valor")) || 0
        : 0;

    valorTotalCampo.value = valorContrato;

    // Atualiza remanescente com base no valor pago
    atualizarRemanescente();
}

// Calcula o saldo remanescente
function atualizarRemanescente() {
    const valorTotal = parseFloat(document.getElementById("valor_total").value) || 0;
    const valorPago = parseFloat(document.getElementById("valor_pago").value) || 0;
    const remanescenteCampo = document.getElementById("remanescente");

    // Fórmula: remanescente = valor_total - valor_pago
    remanescenteCampo.value = valorTotal - valorPago;
}

// Valida antes de enviar o formulário
function validarPagamento() {
    const valorTotal = parseFloat(document.getElementById("valor_total").value) || 0;
    const valorPago = parseFloat(document.getElementById("valor_pago").value) || 0;

    if (valorPago < valorTotal) {
        alert("⚠️ O valor pago não pode ser menor que o valor total.");
        return false; // bloqueia envio
    }
    return true; // permite envio
}
