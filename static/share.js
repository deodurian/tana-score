// Détection du type d'appareil
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

/**
 * Télécharge l'image et retourne un Blob via html2canvas
 */
async function downloadImageAsBlob() {
    let card = document.getElementById('share-card');
    if (!card) {
        card = document.getElementById('share-card-duo');
    }
    
    if (!card) {
        throw new Error("Share card introuvable sur la page.");
    }

    // Afficher temporairement la carte pour html2canvas
    const originalLeft = card.style.left;
    card.style.left = '0px';
    card.style.zIndex = '-9999';

    try {
        const canvas = await html2canvas(card, {
            scale: 1, // On est déjà en 1080x1920
            useCORS: true,
            backgroundColor: null
        });

        return new Promise(resolve => {
            canvas.toBlob(blob => {
                resolve(blob);
            }, 'image/png');
        });
    } finally {
        // Cacher à nouveau
        card.style.left = originalLeft;
    }
}

/**
 * Fonction appelée par le bouton "Télécharger"
 */
async function downloadImage() {
    try {
        // Afficher un petit indicateur de chargement si besoin
        document.body.style.cursor = 'wait';
        
        const blob = await downloadImageAsBlob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'mon_score_tana.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Erreur lors du téléchargement:', error);
        alert("Erreur lors du téléchargement de l'image.");
    } finally {
        document.body.style.cursor = 'default';
    }
}

/**
 * Partage sur Instagram
 */
async function shareToInstagram() {
    try {
        const blob = await downloadImageAsBlob();
        const file = new File([blob], 'tana_score.png', { type: 'image/png' });

        // Sur mobile, utiliser Web Share API si disponible
        if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
            await navigator.share({
                files: [file],
                title: 'Mon Score TANA',
                text: 'Découvre mon score TANA ! 🔥 #TANAscore'
            });
        } else {
            // Sinon, télécharger l'image et afficher un message
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'tana_score.png';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            // Afficher un message
            alert('📸 Image téléchargée ! Ouvre Instagram pour la partager.');

            // Ouvrir Instagram (sur mobile)
            if (isMobile) {
                window.open('instagram://story-camera', '_blank');
            }
        }
    } catch (error) {
        console.error('Erreur lors du partage Instagram:', error);
        alert('Erreur lors du partage. Essaie de télécharger l\'image manuellement.');
    }
}

/**
 * Partage sur Twitter
 */
async function shareToTwitter() {
    try {
        // Récupérer les données du score
        const urlParams = new URLSearchParams(window.location.search);
        const pourcentage = document.querySelector('[name="pourcentage"]')?.value || urlParams.get('pourcentage') || '0';

        // Texte pré-rempli pour Twitter
        const tweetText = `J'ai obtenu ${pourcentage}% au TANA Score ! 🔥 Et toi ? #TANAscore`;
        const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(tweetText)}`;

        // Télécharger l'image
        const blob = await downloadImageAsBlob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'tana_score.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Ouvrir Twitter
        window.open(twitterUrl, '_blank');

        // Message d'information
        setTimeout(() => {
            alert('📸 Image téléchargée ! Tu peux maintenant l\'ajouter à ton tweet.');
        }, 500);

    } catch (error) {
        console.error('Erreur lors du partage Twitter:', error);
        alert('Erreur lors du partage. Essaie de télécharger l\'image manuellement.');
    }
}

/**
 * Copier le lien dans le presse-papier
 */
function copyLink() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(() => {
        alert('✅ Lien copié dans le presse-papier !');
    }).catch(err => {
        console.error('Erreur lors de la copie:', err);
    });
}
