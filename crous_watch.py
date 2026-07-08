name: Surveillance CROUS

on:
  schedule:
    # Toutes les 2 minutes. Attention : GitHub Actions n'execute pas les
    # cron programmes plus frequemment que ~5 minutes dans la pratique
    # (les declenchements trop rapproches sont ignores/retardes,
    # surtout aux heures de forte affluence sur les serveurs GitHub).
    - cron: "*/2 * * * *"
  workflow_dispatch: {}
    # Permet aussi de lancer le script manuellement depuis l'onglet "Actions"
    # de GitHub, pratique pour tester.

permissions:
  contents: write
  # Necessaire pour que le workflow puisse enregistrer l'etat
  # (last_state.json) dans le depot entre deux executions.

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Recuperer le depot
        uses: actions/checkout@v4

      - name: Installer Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Installer les dependances
        run: pip install requests beautifulsoup4

      - name: Lancer la verification
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python crous_watch.py

      - name: Sauvegarder l'etat pour la prochaine verification
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          if [ -f last_state.json ]; then
            git add last_state.json
            git diff --staged --quiet || git commit -m "Mise a jour de l'etat de surveillance [skip ci]"
            git push
          else
            echo "Aucun fichier last_state.json a enregistrer (le script n'a probablement pas pu recuperer la page cette fois-ci)."
          fi
