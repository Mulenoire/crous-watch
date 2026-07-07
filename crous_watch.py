name: Surveillance CROUS

on:
  schedule:
    # Toutes les 2 minutes. Attention : GitHub Actions n'exÃ©cute pas les
    # cron programmÃ©s plus frÃ©quemment que ~5 minutes dans la pratique
    # (les dÃ©clenchements trop rapprochÃ©s sont ignorÃ©s/retardÃ©s,
    # surtout aux heures de forte affluence sur les serveurs GitHub).
    - cron: "*/2 * * * *"
  workflow_dispatch: {}
    # Permet aussi de lancer le script manuellement depuis l'onglet "Actions"
    # de GitHub, pratique pour tester.

permissions:
  contents: write
  # NÃ©cessaire pour que le workflow puisse enregistrer l'Ã©tat
  # (last_state.json) dans le dÃ©pÃ´t entre deux exÃ©cutions.

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: RÃ©cupÃ©rer le dÃ©pÃ´t
        uses: actions/checkout@v4

      - name: Installer Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Installer les dÃ©pendances
        run: pip install requests beautifulsoup4

      - name: Lancer la vÃ©rification
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python crous_watch.py

      - name: Sauvegarder l'Ã©tat pour la prochaine vÃ©rification
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add last_state.json
          git diff --staged --quiet || git commit -m "Mise Ã  jour de l'Ã©tat de surveillance [skip ci]"
          git push
