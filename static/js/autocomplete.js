document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("pesquisaAluno");
  const lista = document.getElementById("sugestoes");

  input.addEventListener("input", () => {
    const termo = input.value;
    if (termo.length > 1) {
      fetch(`/autocomplete_aluno?q=${termo}`)
        .then(res => res.json())
        .then(alunos => {
          lista.innerHTML = "";
          alunos.forEach(aluno => {
            const item = document.createElement("li");
            item.classList.add("list-group-item", "list-group-item-action");
            item.textContent = `${aluno.id} - ${aluno.nome} (${aluno.classe})`;
            item.onclick = () => {
              document.getElementById("id_aluno").value = aluno.id;
              document.getElementById("nome_aluno").value = aluno.nome;
              document.getElementById("classe_aluno").value = aluno.classe;
              document.getElementById("encarregado_aluno").value = aluno.encarregado;
              lista.innerHTML = "";
              input.value = `${aluno.nome}`;
            };
            lista.appendChild(item);
          });
        });
    } else {
      lista.innerHTML = "";
    }
  });
});
