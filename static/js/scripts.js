/* ============================
   📊 Funções de Gráficos (Chart.js)
============================ */

// Gráfico de Barras
function criarGraficoBarras(idCanvas, labels, data, titulo) {
  const ctx = document.getElementById(idCanvas).getContext("2d");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: titulo,
        data: data,
        backgroundColor: "rgba(54, 162, 235, 0.6)",
        borderColor: "rgba(54, 162, 235, 1)",
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        title: { display: true, text: titulo }
      },
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

// Gráfico de Linha
function criarGraficoLinha(idCanvas, labels, data, titulo) {
  const ctx = document.getElementById(idCanvas).getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: titulo,
        data: data,
        fill: false,
        borderColor: "rgba(75, 192, 192, 1)",
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        title: { display: true, text: titulo }
      }
    }
  });
}

// Gráfico de Pizza
function criarGraficoPizza(idCanvas, labels, data, titulo) {
  const ctx = document.getElementById(idCanvas).getContext("2d");
  new Chart(ctx, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [{
        label: titulo,
        data: data,
        backgroundColor: [
          "rgba(255, 99, 132, 0.6)",
          "rgba(54, 162, 235, 0.6)",
          "rgba(255, 206, 86, 0.6)",
          "rgba(75, 192, 192, 0.6)"
        ]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: titulo }
      }
    }
  });
}

/* ============================
   📝 Preenchimento Automático de Alunos
============================ */
document.addEventListener("DOMContentLoaded", function() {
  const pesquisaAluno = document.getElementById("pesquisaAluno");
  if (pesquisaAluno) {
    pesquisaAluno.addEventListener("input", function() {
      const termo = this.value;
      if (termo.length > 2) { // só pesquisa após 3 caracteres
        fetch(`/buscar_aluno?termo=${termo}`)
          .then(res => res.json())
          .then(dados => {
            if (dados && dados.nome) {
              document.getElementById("nomeAluno").value = dados.nome;
              document.getElementById("classeAluno").value = dados.classe;
              document.getElementById("encarregado").value = dados.encarregado;
              document.getElementById("rotaAluno").value = dados.rota;
            }
          })
          .catch(err => console.error("Erro ao buscar aluno:", err));
      }
    });
  }
});

/* ============================
   ⚡ Interações Gerais
============================ */
// Exemplo: alerta de sucesso após cadastro
function mostrarAlerta(mensagem, tipo="success") {
  const alerta = document.createElement("div");
  alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
  alerta.role = "alert";
  alerta.innerHTML = `
    ${mensagem}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.body.prepend(alerta);
  setTimeout(() => alerta.remove(), 5000);
}
