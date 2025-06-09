const questions = document.querySelectorAll('.question');
const ding = document.getElementById('ding');

questions.forEach((q, i) => {
  if (i !== 0) q.style.display = 'none';
});

function playAndNext(i) {
  ding.currentTime = 0;
  ding.play().then(() => {
    showNext(i);
  }).catch(() => {
    showNext(i);
  });
}

function showNext(i) {
  questions[i].style.display = 'none';

  let nextIndex = i + 1;
  while (nextIndex < questions.length && questions[nextIndex].classList.contains('hidden')) {
    nextIndex++;
  }

  if (nextIndex < questions.length) {
    questions[nextIndex].style.display = 'block';
  } else {
    // Affiche explicitement la page résultats
    const resultsQuestion = document.getElementById('q18');
    if (resultsQuestion) {
      questions.forEach(q => q.style.display = 'none');
      resultsQuestion.classList.remove('hidden');
      resultsQuestion.style.display = 'block';
    } else {
      console.log('Fin du questionnaire ou plus de questions visibles');
    }
  }
}

function showFirstVisibleQuestion() {
  for (let i = 0; i < questions.length; i++) {
    if (!questions[i].classList.contains('hidden')) {
      questions.forEach(q => q.style.display = 'none');
      questions[i].style.display = 'block';
      break;
    }
  }
}

function checkAnswerAndNext(i) {
  const question = document.getElementById('q' + i);
  let valid = false;
  const inputs = question.querySelectorAll('input');

  for (const input of inputs) {
    if ((input.type === 'radio' && input.checked) ||
        ((input.type === 'text' || input.type === 'number') && input.value.trim() !== '')) {
      valid = true;
      break;
    }
  }

  if (!valid) {
    alert('Merci de répondre avant de passer à la question suivante.');
    return;
  }
  playAndNext(i);
}

function checkConditionalQuestions() {
  const sexeInputs = document.querySelectorAll('input[name="sexe"]');
  const premierInput = document.querySelector('input[name="premier"]');

  const maquillageQuestion = document.getElementById('q15');
  const bodycountQuestion = document.getElementById('q5');
  const agePlusVieuxQuestion = document.getElementById('q17');
  const tromperQuestions = [
    document.getElementById('q12'),
    document.getElementById('q13'),
    document.getElementById('q14')
  ];
  const resultsQuestion = document.getElementById('q18');

  if (!maquillageQuestion || !bodycountQuestion || !agePlusVieuxQuestion || !premierInput || !resultsQuestion) {
    console.warn('Un ou plusieurs éléments manquent dans le DOM.');
    return;
  }

  function setRequired(question, isRequired) {
    const inputs = question.querySelectorAll('input');
    inputs.forEach(input => {
      if (isRequired) {
        input.setAttribute('required', 'required');
      } else {
        input.removeAttribute('required');
      }
    });
  }

  function updateVisibility() {
    let sexeFemme = false;
    sexeInputs.forEach(input => {
      if (input.checked && input.value === 'f') sexeFemme = true;
    });

    if (sexeFemme) {
      maquillageQuestion.classList.remove('hidden');
      setRequired(maquillageQuestion, true);
    } else {
      maquillageQuestion.classList.add('hidden');
      setRequired(maquillageQuestion, false);
    }

    const premierVal = premierInput.value.trim();
    const showSecondGroup = premierVal !== '' && premierVal !== '0';

    if (showSecondGroup) {
      bodycountQuestion.classList.remove('hidden');
      setRequired(bodycountQuestion, true);
      agePlusVieuxQuestion.classList.remove('hidden');
      setRequired(agePlusVieuxQuestion, true);
      tromperQuestions.forEach(q => {
        if (q) {
          q.classList.remove('hidden');
          setRequired(q, true);
        }
      });
    } else {
      bodycountQuestion.classList.add('hidden');
      setRequired(bodycountQuestion, false);
      agePlusVieuxQuestion.classList.add('hidden');
      setRequired(agePlusVieuxQuestion, false);
      tromperQuestions.forEach(q => {
        if (q) {
          q.classList.add('hidden');
          setRequired(q, false);
        }
      });
    }

    // Toujours afficher la page résultats
    if (resultsQuestion) {
      resultsQuestion.classList.remove('hidden');
    }

    console.log({
      sexeFemme,
      premierVal,
      maquillageAffiche: maquillageQuestion.classList.contains('hidden') ? 'hidden' : 'visible',
      bodycountAffiche: bodycountQuestion.classList.contains('hidden') ? 'hidden' : 'visible',
      agePlusVieuxAffiche: agePlusVieuxQuestion.classList.contains('hidden') ? 'hidden' : 'visible',
      tromperAffiche: tromperQuestions.every(q => q && q.classList.contains('hidden')) ? 'hidden' : 'visible',
      resultsVisible: resultsQuestion.classList.contains('hidden') ? 'hidden' : 'visible'
    });
  }

  sexeInputs.forEach(input => input.addEventListener('change', updateVisibility));
  premierInput.addEventListener('input', updateVisibility);

  updateVisibility();

  // Ajout du comportement pour la question "trompe" (q12)
  const trompeInputs = document.querySelectorAll('input[name="trompe"]');
  trompeInputs.forEach(input => {
    input.addEventListener('change', () => {
      const plaisirQuestion = document.getElementById('q13');
      const refaireQuestion = document.getElementById('q14');

      if (input.value === 'non' && input.checked) {
        // Cacher les questions
        if (plaisirQuestion) plaisirQuestion.classList.add('hidden');
        if (refaireQuestion) refaireQuestion.classList.add('hidden');

        // Cocher "non"
        const plaisirInputs = document.querySelectorAll('input[name="plaisir"]');
        const refaireInputs = document.querySelectorAll('input[name="refaire"]');
        plaisirInputs.forEach(p => {
          if (p.value === 'non') p.checked = true;
        });
        refaireInputs.forEach(r => {
          if (r.value === 'non') r.checked = true;
        });
      } else if (input.value === 'oui' && input.checked) {
        if (plaisirQuestion) plaisirQuestion.classList.remove('hidden');
        if (refaireQuestion) refaireQuestion.classList.remove('hidden');
      }
    });
  });
}

window.onload = () => {
  checkConditionalQuestions();
  showFirstVisibleQuestion();
};


document.querySelectorAll('.button-radio').forEach(button => {
  button.addEventListener('click', () => {
    const name = button.name;
    const group = document.querySelectorAll(`button[name="${name}"]`);
    group.forEach(b => b.classList.remove('selected-button'));
    button.classList.add('selected-button');
  });
});

// Ajout du gestionnaire d'événements pour la touche "Entrée"
document.addEventListener("keydown", function(event) {
  if (event.key === "Enter") {
    event.preventDefault(); // Empêche la soumission du formulaire

    // Trouver la question visible
    let currentIndex = -1;
    questions.forEach((q, i) => {
      if (q.style.display !== 'none') currentIndex = i;
    });

    if (currentIndex === -1) return; // Aucune question visible

    // Vérifier si la réponse est valide
    const question = questions[currentIndex];
    let valid = false;
    const inputs = question.querySelectorAll('input');

    for (const input of inputs) {
      if ((input.type === 'radio' && input.checked) ||
          ((input.type === 'text' || input.type === 'number') && input.value.trim() !== '')) {
        valid = true;
        break;
      }
    }

    if (valid) {
      playAndNext(currentIndex);
    }
  }
});
