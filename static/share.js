// Détection du type d'appareil
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

/**
 * Génère l'URL de l'image de partage
 */
function getShareImageUrl() {
    const urlParams = new URLSearchParams(window.location.search);
    const T = document.querySelector('[name="T"]')?.value || urlParams.get('T') || '0';
    const pourcentage = document.querySelector('[name="pourcentage"]')?.value || urlParams.get('pourcentage') || '0';
    const percentile = document.querySelector('[name="percentile"]')?.value || urlParams.get('percentile') || '0';

    return `/telecharger_image?T=${T}&pourcentage=${pourcentage}&percentile=${percentile}`;
}

/**
 * Télécharge l'image et retourne un Blob
 */
async function downloadImageAsBlob() {
    const imageUrl = getShareImageUrl();
    const response = await fetch(imageUrl);
    const blob = await response.blob();
    return blob;
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
