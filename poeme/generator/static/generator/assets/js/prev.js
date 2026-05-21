const forme_element = document.getElementById("id_forme");
const sylla_element = document.getElementById("id_sylla");

const sonnet = document.getElementById("sonnet");
const haiku = document.getElementById("haiku");
const ballade = document.getElementById("ballade");

sonnet.addEventListener("click", function() {
  forme_element.value = "ABBA CDDC EEF GGF";
  sylla_element.value = "1=12";
});

haiku.addEventListener("click", function() {
  forme_element.value = "ABC";
  sylla_element.value = "1=5, 2=6, 3=5";
});

ballade.addEventListener("click", function() {
  forme_element.value = "ABAB BC CDCD";
  sylla_element.value = "1=10";
});

$(document).ready(function () {
    $('#my-form').submit(function (event) {
        event.preventDefault(); // empêche l'envoi normal du formulaire

        // Afficher le message temporaire
        document.getElementById("telecharger").style.display = "none";
        $('#result').empty();
        $('#err1').empty();
        $('#err2').empty();
        $('#err3').empty();
        $('#status').empty();

        // Récupère le formulaire
        const form = document.getElementById("my-form");

        // Récupère les valeurs des champs de formulaire
        const forme = form.elements["id_forme"].value;
        let sylla = form.elements["id_sylla"].value.replace(/\s+/g, "");
        let phone = form.elements["id_phone"].value.replace(/\s+/g, "");;

        const regexSylla = /^(\d+=\d+)(,\d+=\d+)*,?$/;
        if (sylla != "" && !regexSylla.test(sylla.trim())) {
            $('#err3').html("Les syllabes sont mal renseignées, il faut qu'elles ça soit de la forme : 1=12, 4=8");
            sylla = "";
        }

        // La classe exclut la virgule (0x2C) pour lever l'ambiguïté avec le
        // séparateur "," et éviter un backtracking exponentiel (ReDoS).
        const regexPhone = /^[a-zA-Z]=(?:[\x00-\x2B\x2D-\x7F]+)(,[a-zA-Z]=(?:[\x00-\x2B\x2D-\x7F]+))*,?$/;

        if (phone != "" && !regexPhone.test(phone.trim())) {
            $('#err3').html("Les rimes sont mal renseignées, il faut qu'elles ça soit de la forme : A=t@t, B=se");
            phone = "";
        }

        const previsualisationResultat = prev(forme, sylla, phone);

        const previsualisation = previsualisationResultat[0]
        const err1 = previsualisationResultat[1]
        const err2 = previsualisationResultat[2]

        $('#status').html('Génération du poème en cours...<br/>' + previsualisation);
        $('#err1').html(err1);
        $('#err2').html(err2);

        // Envoyer le formulaire en utilisant AJAX
        $.ajax({
            type: 'POST',
            url: $(this).attr('action'),
            data: $(this).serialize(),
            success: function (response) {
                // Remplacer le message temporaire par le résultat final
                $('#status').empty();

                // Récupérer l'élément avec l'id "result" depuis le code HTML
                const div = document.createElement('div');
                div.innerHTML = response;
                const resultElement = div.querySelector('#result');

                // Récupérer le contenu de la balise <p>
                const resultContent = resultElement.innerHTML.trim();

                $('#result').html(resultContent);
                document.getElementById("telecharger").style.display = "block";


            },
            error: function (xhr, errmsg, err) {
                // Afficher un message d'erreur en cas d'échec du traitement
                $('#err1').html('Erreur : ' + errmsg);
            }
        });
    });
});

function prev(forme = "ABBA", sylltaille = "", rime = "") {
    let err1 = "";
    let err2 = "";

    // Dictionnaire des noms de syllabes correspondant aux syllabes données
    let syllname = {};
    let nbsyll = [];

    if (forme.length !== 0) {
        if (sylltaille.length !== 0) {
            // Création liste nbsyll
            sylltaille = sylltaille.split(",");
            nbsyll = Array(forme.replace(" ", "").length).fill("");
            for (let i = 0; i < sylltaille.length; i++) {
                let syllUnit1 = sylltaille[i];
                let syllUnit2 = syllUnit1.replace(" ", "").split("=");
                try {
                    parseInt(syllUnit2[0]);
                    parseInt(syllUnit2[1]);
                } catch (err) {
                    // Si problème dans la façon dont est la taille des syllabes
                    err1 = syllUnit1 + " est mal écrit";
                    err2 = "Veuillez respecter la mise en forme :\n 1=12, 2=6 ...";
                    return [null, err1, err2];
                }
                try {
                    if (parseInt(syllUnit2[1]) > 12) {
                        // Si nb syllabe dépasse 12
                        err1 = "Attention, nombre de syllabes max dépassés\n(max = 12)";
                        nbsyll[parseInt(syllUnit2[0]) - 1] = "_ ".repeat(11);
                    } else if (parseInt(syllUnit2[1]) < 1) {
                        // Si nb syllabe inférieur à 1
                        err1 = "Attention, nombre de syllabes min = 1";
                        nbsyll[parseInt(syllUnit2[0]) - 1] = " ";
                    } else if (parseInt(syllUnit2[1]) === 1) {
                        // Si nb syllabe = 1
                        nbsyll[parseInt(syllUnit2[0]) - 1] = " ";
                    } else {
                        // Sinon
                        nbsyll[parseInt(syllUnit2[0]) - 1] = "_ ".repeat(
                            parseInt(syllUnit2[1]) - 1
                        );
                    }
                } catch (err) {
                    // Si nb syllabe dépasse nombre vers
                    err1 = "Vous avez dépassé le nombre de vers donnés dans la forme";
                    return [null, err1, err2];
                }
            }
            // Pas de probleme : créer les str avec les _ suivant le nb de syllabes
            if (nbsyll[0] === "") {
                nbsyll[0] = "_ ".repeat(11);
            } else if (nbsyll[0] === " ") {
                nbsyll[0] = "";
            }
            for (let a = 1; a < nbsyll.length; a++) {
                if (nbsyll[a] === "") {
                    nbsyll[a] = "_ ".repeat(nbsyll[a - 1].split("_").length - 1);
                }
            }
        } else {
            // Si aucune info sur le nombre de syllabe donnée
            nbsyll = Array(forme.replace(" ", "").length).fill("_ ".repeat(11));
        }
        let texte = "";
        if (rime.length === 0) {
            // Sans rimes forcées, juste avec forme
            let j = 0;
            for (let i = 0; i < forme.length; i++) {
                if (forme[i] === " ") {
                    texte += '\n';
                } else {
                    texte += nbsyll[j] + forme[i] + "\n";
                    j++;
                }
            }
        } else {
            // Avec rimes forcées
            rime.split(",").forEach((rimeUnit) => {
                let a = rimeUnit.replace(" ", "").split("=");
                if (forme.includes(a[0])) {
                    syllname[a[0]] = a[1];
                } else {
                    // Si erreur sur la façon dont sont données les rimes
                    let err1 = "Les rimes sont mal écrites";
                    let err2 = "Veuillez respecter la mise en forme : A=t@t, B=se … (avec les bons symboles " +
                        "correspondants à ceux donnés dans forme)";
                    return [null, err1, err2];
                }
            });

            let j = 0;
            for (let i = 0; i < forme.length; i++) {
                if (forme[i] === " ") {
                    texte += '\n';
                } else {
                    if (syllname[forme[i]]) {
                        texte += nbsyll[j] + syllname[forme[i]] + ".\n";
                    } else {
                        texte += nbsyll[j] + forme[i] + "\n";
                    }
                    j++;
                }
            }
        }

        if (!forme) {
            // Si aucune forme n'est donnée
            let err1 = "Vous n'avez donné aucune forme";
            return [null, err1, err2];
        }

        forme = forme.replace(" ", ""); // Variable globale de la forme pour être affiché dans chargement
        return [texte.split("\n").join("<br/>"), err1, err2];
    }
}
function download() {
  const content = document.getElementById("result").textContent;
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "mypoem.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}