const questions = document.querySelectorAll('.question');
const ding = document.getElementById('ding');

// Tracking du temps de complétion
let quizStartTime = Date.now();
let navigationHistory = []; // Historique pour le bouton retour

questions.forEach((q, i) => {
  if (i !== 0) {
    q.style.display = 'none';
  } else {
    q.style.display = 'flex';
  }
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
  let nextIndex = i + 1;
  while (nextIndex < questions.length && questions[nextIndex].classList.contains('hidden')) {
    nextIndex++;
  }

  if (nextIndex < questions.length) {
    // Animation de sortie vers la gauche
    questions[i].classList.remove('slide-in-right', 'slide-in-left');
    questions[i].classList.add('slide-out-left');
    
    // Après l'animation, masquer complètement
    setTimeout(() => {
      questions[i].style.display = 'none';
      questions[i].classList.remove('slide-out-left');
    }, 400);

    // Animation d'entrée depuis la droite
    questions[nextIndex].style.display = 'flex';
    questions[nextIndex].classList.remove('slide-out-left', 'slide-out-right', 'hidden');
    questions[nextIndex].classList.add('slide-in-right');
    
    navigationHistory.push(nextIndex); // Ajouter à l'historique
  } else {
    // Affiche explicitement la page résultats
    const resultsQuestion = document.getElementById('q18');
    if (resultsQuestion) {
      questions[i].classList.add('slide-out-left');
      setTimeout(() => {
        questions.forEach(q => {
          q.style.display = 'none';
          q.classList.remove('slide-out-left', 'slide-in-right');
        });
        resultsQuestion.classList.remove('hidden');
        resultsQuestion.style.display = 'flex';
        resultsQuestion.classList.add('slide-in-right');
      }, 400);
    } else {
      console.log('Fin du questionnaire ou plus de questions visibles');
    }
  }
}

function showPrevious(currentIndex) {
  // Retirer la question actuelle de l'historique
  if (navigationHistory.length > 0) {
    navigationHistory.pop();
  }

  // Trouver la question précédente visible
  let prevIndex = currentIndex - 1;
  while (prevIndex >= 0 && questions[prevIndex].classList.contains('hidden')) {
    prevIndex--;
  }

  if (prevIndex >= 0) {
    // Animation de sortie vers la droite
    questions[currentIndex].classList.remove('slide-in-right', 'slide-in-left');
    questions[currentIndex].classList.add('slide-out-right');
    
    setTimeout(() => {
      questions[currentIndex].style.display = 'none';
      questions[currentIndex].classList.remove('slide-out-right');
    }, 400);

    // Animation d'entrée depuis la gauche
    questions[prevIndex].style.display = 'flex';
    questions[prevIndex].classList.remove('slide-out-left', 'slide-out-right', 'hidden');
    questions[prevIndex].classList.add('slide-in-left');
  }
}

function showFirstVisibleQuestion() {
  for (let i = 0; i < questions.length; i++) {
    if (!questions[i].classList.contains('hidden')) {
      questions.forEach(q => {
        q.style.display = 'none';
        q.classList.remove('slide-out-left', 'slide-out-right', 'slide-in-left', 'slide-in-right');
      });
      questions[i].style.display = 'flex';
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
document.addEventListener("keydown", function (event) {
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

// Calculer et injecter le temps de complétion lors de la soumission
document.getElementById('tanaForm').addEventListener('submit', function (e) {
  // Désactiver le bouton d'envoi pour éviter les clics multiples
  const submitBtn = this.querySelector('button[type="submit"]');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerText = "Calcul en cours...";
    submitBtn.style.opacity = "0.7";
    submitBtn.style.cursor = "wait";
  }

  const completionTime = Math.floor((Date.now() - quizStartTime) / 1000); // en secondes

  // Formater le temps (ex: "2min 34s")
  const minutes = Math.floor(completionTime / 60);
  const seconds = completionTime % 60;
  const formattedTime = minutes > 0 ? `${minutes}min ${seconds}s` : `${seconds}s`;

  // Injecter dans le champ caché
  document.getElementById('completionTime').value = formattedTime;
});
