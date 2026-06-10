const questions = document.querySelectorAll('.question');
const ding = document.getElementById('ding');

// Tracking du temps de complétion
let quizStartTime = Date.now();
let navigationHistory = []; // Historique pour le bouton retour

// Initialiser le Mode Duo
function initDuoMode() {
  questions.forEach((q, i) => {
    const content = q.querySelector('.content-question');
    if (content) {
      // Wrapper
      const wrapper = document.createElement('div');
      wrapper.className = 'duo-wrapper';
      wrapper.style.display = 'flex';
      wrapper.style.gap = '20px';
      wrapper.style.width = '100%';
      wrapper.style.justifyContent = 'space-between';

      // Joueur 1
      const p1 = document.createElement('div');
      p1.className = 'player-container-1';
      p1.style.flex = '1';
      p1.style.backgroundColor = 'rgba(255, 105, 180, 0.1)';
      p1.style.padding = '15px';
      p1.style.borderRadius = '12px';
      
      const p1Header = document.createElement('h3');
      p1Header.innerText = 'Toi';
      p1Header.style.color = '#ff69b4';
      p1Header.style.marginBottom = '15px';
      p1.appendChild(p1Header);
      
      const p1Content = content.cloneNode(true);
      p1Content.querySelectorAll('input').forEach(inp => {
        inp.name = inp.name + '_1';
        if (inp.id) inp.id = inp.id + '_1';
      });
      p1Content.querySelectorAll('label').forEach(lbl => {
        if (lbl.htmlFor) lbl.htmlFor = lbl.htmlFor + '_1';
      });
      p1.appendChild(p1Content);

      // Joueur 2
      const p2 = document.createElement('div');
      p2.className = 'player-container-2';
      p2.style.flex = '1';
      p2.style.backgroundColor = 'rgba(0, 122, 204, 0.1)';
      p2.style.padding = '15px';
      p2.style.borderRadius = '12px';
      
      const p2Header = document.createElement('h3');
      p2Header.innerText = 'Ton/Ta Partenaire';
      p2Header.style.color = '#007acc';
      p2Header.style.marginBottom = '15px';
      p2.appendChild(p2Header);
      
      const p2Content = content.cloneNode(true);
      p2Content.querySelectorAll('input').forEach(inp => {
        inp.name = inp.name + '_2';
        if (inp.id) inp.id = inp.id + '_2';
      });
      p2Content.querySelectorAll('label').forEach(lbl => {
        if (lbl.htmlFor) lbl.htmlFor = lbl.htmlFor + '_2';
      });
      p2.appendChild(p2Content);

      wrapper.appendChild(p1);
      wrapper.appendChild(p2);

      q.insertBefore(wrapper, content);
      content.remove();
    }
  });
}

initDuoMode();

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
    questions[i].classList.remove('slide-in-right', 'slide-in-left');
    questions[i].classList.add('slide-out-left');
    
    setTimeout(() => {
      questions[i].style.display = 'none';
      questions[i].classList.remove('slide-out-left');
    }, 400);

    questions[nextIndex].style.display = 'flex';
    questions[nextIndex].classList.remove('slide-out-left', 'slide-out-right', 'hidden');
    questions[nextIndex].classList.add('slide-in-right');
    
    navigationHistory.push(nextIndex);
  } else {
    const resultsQuestion = document.getElementById('q23');
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
    }
  }
}

function showPrevious(currentIndex) {
  if (navigationHistory.length > 0) {
    navigationHistory.pop();
  }

  let prevIndex = currentIndex - 1;
  while (prevIndex >= 0 && questions[prevIndex].classList.contains('hidden')) {
    prevIndex--;
  }

  if (prevIndex >= 0) {
    questions[currentIndex].classList.remove('slide-in-right', 'slide-in-left');
    questions[currentIndex].classList.add('slide-out-right');
    
    setTimeout(() => {
      questions[currentIndex].style.display = 'none';
      questions[currentIndex].classList.remove('slide-out-right');
    }, 400);

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
  let valid = true;

  const containers = [
    question.querySelector('.player-container-1'),
    question.querySelector('.player-container-2')
  ];

  for (const container of containers) {
    // On ne vérifie que si l'encadré du joueur est visible
    if (container && container.style.display !== 'none' && container.style.visibility !== 'hidden') {
      const inputs = container.querySelectorAll('input');
      let containerHasAnswer = false;
      let hasVisibleInputs = false;

      for (const input of inputs) {
        if (input.type === 'hidden') continue;
        hasVisibleInputs = true;
        
        if ((input.type === 'radio' && input.checked) ||
            ((input.type === 'text' || input.type === 'number') && input.value.trim() !== '')) {
          containerHasAnswer = true;
          break; // Dès qu'une réponse est donnée, c'est bon pour ce joueur
        }
      }
      
      // Si le joueur a des champs à remplir mais n'a rien rempli
      if (hasVisibleInputs && !containerHasAnswer) {
        valid = false;
      }
    }
  }

  if (!valid) {
    alert('Les deux joueurs doivent répondre avant de passer à la question suivante.');
    return;
  }

  // Vérification de l'âge (Question 1)
  if (i === 1) {
    let ageValid = true;
    for (const container of containers) {
      if (container && container.style.display !== 'none' && container.style.visibility !== 'hidden') {
        const inputs = container.querySelectorAll('input');
        for (const input of inputs) {
          if (input.type === 'number' && input.name.startsWith('age')) {
            const ageVal = parseInt(input.value);
            if (ageVal < 13 || ageVal > 100) {
              ageValid = false;
            }
          }
        }
      }
    }
    if (!ageValid) {
      alert("Désolé, les deux joueurs doivent avoir au moins 13 ans pour faire ce test.");
      return;
    }
  }

  playAndNext(i);
}

function checkConditionalQuestions() {
  function updatePlayerVis(suffix) {
    const sexeInputs = document.querySelectorAll(`input[name="sexe_${suffix}"]`);
    const premierInput = document.querySelector(`input[name="premier_${suffix}"]`);
    
    let sexeFemme = false;
    sexeInputs.forEach(input => {
      if (input.checked && input.value === 'f') sexeFemme = true;
    });

    const maquillageQuestion = document.querySelector(`#q15 .player-container-${suffix}`);
    if (maquillageQuestion) {
      if (sexeFemme) {
        maquillageQuestion.style.display = 'block';
        maquillageQuestion.querySelectorAll('input').forEach(i => i.setAttribute('required', 'required'));
      } else {
        maquillageQuestion.style.display = 'none';
        maquillageQuestion.querySelectorAll('input').forEach(i => i.removeAttribute('required'));
      }
    }

    const premierVal = premierInput ? premierInput.value.trim() : '';
    const showSecondGroup = premierVal !== '' && premierVal !== '0';

    const tromperQs = [
      document.querySelector(`#q5 .player-container-${suffix}`),
      document.querySelector(`#q17 .player-container-${suffix}`),
      document.querySelector(`#q12 .player-container-${suffix}`),
      document.querySelector(`#q13 .player-container-${suffix}`),
      document.querySelector(`#q14 .player-container-${suffix}`)
    ];

    tromperQs.forEach(q => {
      if (q) {
        if (showSecondGroup) {
          q.style.display = 'block';
          q.querySelectorAll('input').forEach(i => {
              if(i.hasAttribute('data-was-required')) i.setAttribute('required', 'required');
          });
        } else {
          q.style.display = 'none';
          q.querySelectorAll('input').forEach(i => {
              if(i.hasAttribute('required')) i.setAttribute('data-was-required', 'true');
              i.removeAttribute('required');
          });
        }
      }
    });
    
    // Logique trompe oui/non
    const trompeInputs = document.querySelectorAll(`input[name="trompe_${suffix}"]`);
    trompeInputs.forEach(input => {
      input.addEventListener('change', () => {
        const plaisirQuestion = document.querySelector(`#q13 .player-container-${suffix}`);
        const refaireQuestion = document.querySelector(`#q14 .player-container-${suffix}`);
        if (input.value === 'non' && input.checked) {
          if (plaisirQuestion) plaisirQuestion.style.display = 'none';
          if (refaireQuestion) refaireQuestion.style.display = 'none';
          document.querySelectorAll(`input[name="plaisir_${suffix}"]`).forEach(p => { if(p.value==='non') p.checked = true; });
          document.querySelectorAll(`input[name="refaire_${suffix}"]`).forEach(p => { if(p.value==='non') p.checked = true; });
        } else if (input.value === 'oui' && input.checked) {
          if (plaisirQuestion) plaisirQuestion.style.display = 'block';
          if (refaireQuestion) refaireQuestion.style.display = 'block';
        }
      });
    });
  }

  updatePlayerVis('1');
  updatePlayerVis('2');

  function updateParentVis(qId) {
    const q = document.getElementById(qId);
    if (!q) return;
    const p1 = document.querySelector(`#${qId} .player-container-1`);
    const p2 = document.querySelector(`#${qId} .player-container-2`);
    if (p1 && p2) {
      if (p1.style.display === 'none' && p2.style.display === 'none') {
        q.classList.add('hidden');
      } else {
        q.classList.remove('hidden');
      }
    }
  }

  ['q15', 'q5', 'q17', 'q12', 'q13', 'q14'].forEach(updateParentVis);
}

let listenersAttached = false;
function attachListeners() {
    if(listenersAttached) return;
    document.querySelectorAll(`input[name^="sexe_"]`).forEach(i => i.addEventListener('change', checkConditionalQuestions));
    document.querySelectorAll(`input[name^="premier_"]`).forEach(i => i.addEventListener('input', checkConditionalQuestions));
    listenersAttached = true;
}

window.onload = () => {
  document.querySelectorAll('input[required]').forEach(i => i.setAttribute('data-was-required', 'true'));
  checkConditionalQuestions();
  attachListeners();
  showFirstVisibleQuestion();
};

document.getElementById('tanaForm').addEventListener('submit', function (e) {
  const submitBtn = this.querySelector('button[type="submit"]');
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerText = "Calcul en cours...";
    submitBtn.style.opacity = "0.7";
    submitBtn.style.cursor = "wait";
  }

  const completionTime = Math.floor((Date.now() - quizStartTime) / 1000);
  const minutes = Math.floor(completionTime / 60);
  const seconds = completionTime % 60;
  const formattedTime = minutes > 0 ? `${minutes}min ${seconds}s` : `${seconds}s`;
  document.getElementById('completionTime').value = formattedTime;
});

document.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();
  }
});
