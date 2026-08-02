const PLAYER_STORAGE_KEY =
  "tasmania-hackentrick-player";

const footerStatus =
  document.getElementById("footer-status");

let appData = null;
let latestMatchday = null;
let selectedMatchday = null;
let selectedSeasonMatchday = null;
let selectedPlayer = null;
let activeView = "season";

function updateConnectionStatus() {
  const baseStatus =
    footerStatus.dataset.baseStatus ||
    footerStatus.textContent;

  footerStatus.textContent = navigator.onLine
    ? baseStatus
    : `${baseStatus} · Offline – letzter gespeicherter Stand`;
}

const seasonTab =
  document.getElementById("season-tab");

const matchdayTab =
  document.getElementById("matchday-tab");

const matchdayControls =
  document.getElementById("matchday-controls");

const matchdaySelect =
  document.getElementById("matchday-select");

const seasonMatchdaySelect =
  document.getElementById("season-matchday-select");

const hero =
  document.getElementById("hero");

const summary =
  document.getElementById("summary");

const rankingHeading =
  document.getElementById("ranking-heading");

const loading =
  document.getElementById("loading");

const desktopRanking =
  document.getElementById("desktop-ranking");

const mobileRanking =
  document.getElementById("mobile-ranking");

const playerDialogBackdrop =
  document.getElementById("player-dialog-backdrop");

const playerSelect =
  document.getElementById("player-select");

const savePlayerButton =
  document.getElementById("save-player-button");

const cancelPlayerButton =
  document.getElementById("cancel-player-button");

const changePlayerButton =
  document.getElementById("change-player-button");

seasonTab.addEventListener("click", () => {
  setView("season");
});

matchdayTab.addEventListener("click", () => {
  setView("matchday");
});

matchdaySelect.addEventListener(
  "change",
  event => {
    selectedMatchday =
      Number(event.target.value);

    renderMatchdayView();
  }
);

seasonMatchdaySelect.addEventListener(
  "change",
  event => {
    selectedSeasonMatchday =
      Number(event.target.value);

    renderSeasonView();
  }
);

savePlayerButton.addEventListener(
  "click",
  () => {
    const player = playerSelect.value;

    if (!player) {
      return;
    }

    selectedPlayer = player;

    localStorage.setItem(
      PLAYER_STORAGE_KEY,
      selectedPlayer
    );

    closePlayerDialog();
    renderActiveView();
  }
);

cancelPlayerButton.addEventListener(
  "click",
  closePlayerDialog
);

changePlayerButton.addEventListener(
  "click",
  () => {
    openPlayerDialog(true);
  }
);

function setView(view) {
  activeView = view;

  seasonTab.classList.toggle(
    "active",
    view === "season"
  );

  matchdayTab.classList.toggle(
    "active",
    view === "matchday"
  );

  renderActiveView();
}

function createSummaryCard(
  label,
  value,
  accent = "navy"
) {
  return `
    <article
      class="card summary-card ${accent}-accent"
    >
      <div class="summary-label">
        ${label}
      </div>

      <div class="summary-value">
        ${value}
      </div>
    </article>
  `;
}

function getSortedMatchdayNumbers() {
  return appData.matchdays
    .map(item => Number(item.matchday))
    .sort((a, b) => a - b);
}

function getLatestMatchday(matchdays) {
  return [...matchdays].sort(
    (a, b) =>
      Number(b.matchday) -
      Number(a.matchday)
  )[0];
}

function formatDateOnly(value) {
  if (!value) {
    return "–";
  }

  return new Intl.DateTimeFormat(
    "de-DE",
    {
      day: "2-digit",
      month: "2-digit",
      year: "numeric"
    }
  ).format(new Date(value));
}

function namesWithMaximum(
  results,
  getValue,
  separator = ", "
) {
  const maximum = Math.max(
    ...results.map(getValue)
  );

  return results
    .filter(
      result =>
        getValue(result) === maximum
    )
    .map(result => result.name)
    .join(separator);
}

function assignCompetitionRanks(
  rows,
  pointsField
) {
  const sorted = [...rows].sort(
    (a, b) => {
      const difference =
        Number(b[pointsField]) -
        Number(a[pointsField]);

      if (difference !== 0) {
        return difference;
      }

      return a.name.localeCompare(
        b.name,
        "de",
        { sensitivity: "base" }
      );
    }
  );

  let previousPoints = null;
  let currentRank = 0;

  return sorted.map(
    (row, index) => {
      const points =
        Number(row[pointsField]);

      if (points !== previousPoints) {
        currentRank = index + 1;
      }

      previousPoints = points;

      return {
        ...row,
        rank: currentRank
      };
    }
  );
}

function calculateSeasonRanking(
  data,
  maximumMatchday
) {
  const totals = new Map();

  for (const name of data.participants) {
    totals.set(name, {
      name,
      tsPoints: 0,
      msPoints: 0,
      totalPoints: 0,
      matchdayWins: 0
    });
  }

  const relevantMatchdays =
    data.matchdays.filter(
      matchday =>
        Number(matchday.matchday) <=
        Number(maximumMatchday)
    );

  for (const matchday of relevantMatchdays) {
    for (const result of matchday.results) {
      const participant =
        totals.get(result.name);

      if (!participant) {
        continue;
      }

      participant.tsPoints +=
        Number(result.ts.points);

      participant.msPoints +=
        Number(result.ms.points);

      participant.totalPoints +=
        Number(result.matchday_points);

      if (
        Number(result.matchday_rank) === 1
      ) {
        participant.matchdayWins += 1;
      }
    }
  }

  return assignCompetitionRanks(
    [...totals.values()],
    "totalPoints"
  );
}

function getPreviousAvailableMatchday(
  selectedNumber
) {
  const earlierMatchdays =
    getSortedMatchdayNumbers().filter(
      number =>
        number < Number(selectedNumber)
    );

  if (earlierMatchdays.length === 0) {
    return null;
  }

  return earlierMatchdays[
    earlierMatchdays.length - 1
  ];
}

function getSeasonRankingWithTrend(
  selectedNumber
) {
  const currentRanking =
    calculateSeasonRanking(
      appData,
      selectedNumber
    );

  const previousNumber =
    getPreviousAvailableMatchday(
      selectedNumber
    );

  if (previousNumber === null) {
    return currentRanking.map(result => ({
      ...result,
      trend: 0
    }));
  }

  const previousRanking =
    calculateSeasonRanking(
      appData,
      previousNumber
    );

  const previousRanks = new Map(
    previousRanking.map(result => [
      result.name,
      result.rank
    ])
  );

  return currentRanking.map(result => ({
    ...result,
    trend:
      Number(previousRanks.get(result.name)) -
      Number(result.rank)
  }));
}

function populateMatchdaySelect() {
  const sortedMatchdays =
    [...appData.matchdays].sort(
      (a, b) =>
        Number(b.matchday) -
        Number(a.matchday)
    );

  const options = sortedMatchdays
    .map(
      matchday => `
        <option value="${matchday.matchday}">
          Spieltag ${matchday.matchday}
        </option>
      `
    )
    .join("");

  matchdaySelect.innerHTML = options;
  seasonMatchdaySelect.innerHTML = options;

  matchdaySelect.value =
    String(selectedMatchday);

  seasonMatchdaySelect.value =
    String(selectedSeasonMatchday);
}

function populatePlayerSelect() {
  playerSelect.innerHTML = `
    <option value="">
      Bitte auswählen
    </option>
    ${appData.participants
      .map(
        name => `
          <option value="${name}">
            ${name}
          </option>
        `
      )
      .join("")}
  `;

  if (selectedPlayer) {
    playerSelect.value = selectedPlayer;
  }
}

function openPlayerDialog(canCancel) {
  populatePlayerSelect();

  cancelPlayerButton.hidden = !canCancel;
  playerDialogBackdrop.hidden = false;

  window.setTimeout(() => {
    playerSelect.focus();
  }, 0);
}

function closePlayerDialog() {
  playerDialogBackdrop.hidden = true;
}

function getRankClass(rank) {
  const numericRank = Number(rank);

  if (numericRank === 1) {
    return "rank-1";
  }

  if (numericRank === 2) {
    return "rank-2";
  }

  if (numericRank === 3) {
    return "rank-3";
  }

  return "";
}

function getPodiumRowClass(rank) {
  const numericRank = Number(rank);

  if (
    numericRank >= 1 &&
    numericRank <= 3
  ) {
    return `podium-${numericRank}`;
  }

  return "";
}

function getTrendMarkup(trend) {
  if (trend > 0) {
    return `
      <span class="trend trend-up">
        ▲ ${trend}
      </span>
    `;
  }

  if (trend < 0) {
    return `
      <span class="trend trend-down">
        ▼ ${Math.abs(trend)}
      </span>
    `;
  }

  return `
    <span class="trend trend-same">
      –
    </span>
  `;
}

function getYouBadge(name) {
  return name === selectedPlayer
    ? `<span class="you-badge">Du</span>`
    : "";
}

function isSelectedPlayer(name) {
  return name === selectedPlayer;
}

function renderActiveView() {
  if (!appData || !latestMatchday) {
    return;
  }

  if (activeView === "season") {
    renderSeasonView();
  } else {
    renderMatchdayView();
  }
}

function renderSeasonView() {
  matchdayControls.hidden = true;
  hero.hidden = true;
  summary.hidden = true;
  rankingHeading.hidden = false;

  seasonMatchdaySelect.value =
    String(selectedSeasonMatchday);

  const ranking =
    getSeasonRankingWithTrend(
      selectedSeasonMatchday
    );

  document.getElementById(
    "ranking-title"
  ).textContent = "Gesamtwertung";

  document.getElementById(
    "ranking-head"
  ).innerHTML = `
    <tr>
      <th>Rang</th>
      <th>Spieler</th>
      <th>TS</th>
      <th>MS</th>
      <th>Gesamt</th>
      <th>Tagessiege</th>
      <th>Trend</th>
    </tr>
  `;

  document.getElementById(
    "ranking-body"
  ).innerHTML =
    ranking
      .map(result => {
        const rankClass =
          getRankClass(result.rank);

        const rowClasses = [
          getPodiumRowClass(result.rank),
          isSelectedPlayer(result.name)
            ? "is-me"
            : ""
        ]
          .filter(Boolean)
          .join(" ");

        return `
          <tr class="${rowClasses}">
            <td>
              <span
                class="rank-badge ${rankClass}"
              >
                ${result.rank}
              </span>
            </td>

            <td class="player">
              ${result.name}
              ${getYouBadge(result.name)}
            </td>

            <td class="ts-value">
              ${result.tsPoints}
            </td>

            <td class="ms-value">
              ${result.msPoints}
            </td>

            <td class="total">
              ${result.totalPoints}
            </td>

            <td>
              ${result.matchdayWins}
            </td>

            <td>
              ${getTrendMarkup(result.trend)}
            </td>
          </tr>
        `;
      })
      .join("");

  document.getElementById(
    "mobile-ranking-list"
  ).innerHTML =
    ranking
      .map(result => {
        const rankClass =
          getRankClass(result.rank);

        const selectedClass =
          isSelectedPlayer(result.name)
            ? "is-me"
            : "";

        return `
          <article
            class="
              ranking-item
              place-${result.rank}
              ${selectedClass}
            "
          >
            <span
              class="rank-badge ${rankClass}"
            >
              ${result.rank}
            </span>

            <div class="mobile-player">
              <div class="mobile-player-name">
                ${result.name}
                ${getYouBadge(result.name)}
              </div>

              <div class="mobile-details">
                <span class="points-badge ts">
                  TS ${result.tsPoints}
                </span>

                <span class="points-badge ms">
                  MS ${result.msPoints}
                </span>

                <span>
                  ${result.matchdayWins}
                  Tagessieg${
                    result.matchdayWins === 1
                      ? ""
                      : "e"
                  }
                </span>
              </div>
            </div>

            <div class="mobile-total">
              ${result.totalPoints}

              <span class="mobile-total-label">
                Punkte
              </span>

              <div class="mobile-trend">
                ${getTrendMarkup(result.trend)}
              </div>
            </div>
          </article>
        `;
      })
      .join("");
}

function renderMatchdayView() {
  matchdayControls.hidden = false;
  hero.hidden = false;
  summary.hidden = false;
  rankingHeading.hidden = true;

  const matchday =
    appData.matchdays.find(
      item =>
        Number(item.matchday) ===
        Number(selectedMatchday)
    );

  if (!matchday) {
    return;
  }

  matchdaySelect.value =
    String(matchday.matchday);

  const results =
    [...matchday.results].sort(
      (a, b) => {
        const rankDifference =
          Number(a.matchday_rank) -
          Number(b.matchday_rank);

        if (rankDifference !== 0) {
          return rankDifference;
        }

        return a.name.localeCompare(
          b.name,
          "de",
          { sensitivity: "base" }
        );
      }
    );

  const winnerNames =
    namesWithMaximum(
      results,
      result =>
        result.matchday_points,
      " & "
    );

  const bestTs =
    namesWithMaximum(
      results,
      result =>
        result.ts.points,
      " & "
    );

  const bestMs =
    namesWithMaximum(
      results,
      result =>
        result.ms.points,
      " & "
    );

  document.getElementById(
    "hero-label"
  ).textContent = "Mann des Tages";

  document.getElementById(
    "hero-value"
  ).textContent = winnerNames;

  summary.innerHTML = [
    createSummaryCard(
      "Bestes Tippspiel",
      bestTs,
      "red"
    ),
    createSummaryCard(
      "Bestes Managerspiel",
      bestMs,
      "navy"
    )
  ].join("");

  document.getElementById(
    "ranking-head"
  ).innerHTML = `
    <tr>
      <th>Rang</th>
      <th>Spieler</th>
      <th>TS</th>
      <th>MS</th>
      <th>Gesamt</th>
      <th>Rohpunkte</th>
    </tr>
  `;

  document.getElementById(
    "ranking-body"
  ).innerHTML =
    results
      .map(result => {
        const rankClass =
          getRankClass(
            result.matchday_rank
          );

        const rowClasses = [
          getPodiumRowClass(
            result.matchday_rank
          ),
          isSelectedPlayer(result.name)
            ? "is-me"
            : ""
        ]
          .filter(Boolean)
          .join(" ");

        return `
          <tr class="${rowClasses}">
            <td>
              <span
                class="rank-badge ${rankClass}"
              >
                ${result.matchday_rank}
              </span>
            </td>

            <td class="player">
              ${result.name}
              ${getYouBadge(result.name)}
            </td>

            <td class="ts-value">
              ${result.ts.points}
            </td>

            <td class="ms-value">
              ${result.ms.points}
            </td>

            <td class="total">
              ${result.matchday_points}
            </td>

            <td class="raw">
              TS ${result.ts.raw_points}
              ·
              MS ${result.ms.raw_points}
            </td>
          </tr>
        `;
      })
      .join("");

  document.getElementById(
    "mobile-ranking-list"
  ).innerHTML =
    results
      .map(result => {
        const rankClass =
          getRankClass(
            result.matchday_rank
          );

        const selectedClass =
          isSelectedPlayer(result.name)
            ? "is-me"
            : "";

        return `
          <article
            class="
              ranking-item
              place-${result.matchday_rank}
              ${selectedClass}
            "
          >
            <span
              class="rank-badge ${rankClass}"
            >
              ${result.matchday_rank}
            </span>

            <div class="mobile-player">
              <div class="mobile-player-name">
                ${result.name}
                ${getYouBadge(result.name)}
              </div>

              <div class="mobile-details">
                <span class="points-badge ts">
                  TS ${result.ts.points}
                </span>

                <span class="points-badge ms">
                  MS ${result.ms.points}
                </span>

                <span>
                  Roh:
                  ${result.ts.raw_points}
                  /
                  ${result.ms.raw_points}
                </span>
              </div>
            </div>

            <div class="mobile-total">
              ${result.matchday_points}

              <span class="mobile-total-label">
                Punkte
              </span>
            </div>
          </article>
        `;
      })
      .join("");
}

async function loadData() {
  try {
    const response = await fetch(
      `data.json?timestamp=${Date.now()}`,
      {
        cache: "no-store"
      }
    );

    if (!response.ok) {
      throw new Error(
        "data.json konnte nicht geladen werden: " +
        response.status
      );
    }

    appData = await response.json();

    if (
      !Array.isArray(appData.matchdays) ||
      appData.matchdays.length === 0
    ) {
      throw new Error(
        "Es sind noch keine Spieltage gespeichert."
      );
    }

    if (
      !Array.isArray(appData.participants) ||
      appData.participants.length !== 9
    ) {
      throw new Error(
        "Die Teilnehmerliste ist nicht vollständig."
      );
    }

    latestMatchday =
      getLatestMatchday(
        appData.matchdays
      );

    if (
      !Array.isArray(
        latestMatchday.results
      ) ||
      latestMatchday.results.length !== 9
    ) {
      throw new Error(
        "Die Spieltagsdaten sind nicht vollständig."
      );
    }

    selectedMatchday =
      Number(latestMatchday.matchday);

    selectedSeasonMatchday =
      Number(latestMatchday.matchday);

    const storedPlayer =
      localStorage.getItem(
        PLAYER_STORAGE_KEY
      );

    if (
      storedPlayer &&
      appData.participants.includes(
        storedPlayer
      )
    ) {
      selectedPlayer = storedPlayer;
    }

    populateMatchdaySelect();
    renderActiveView();

    loading.hidden = true;
    desktopRanking.hidden = false;
    mobileRanking.hidden = false;

    footerStatus.dataset.baseStatus =
      `Stand: ${latestMatchday.matchday}. Spieltag` +
      ` · ${formatDateOnly(appData.updated_at)}`;

    updateConnectionStatus();

    changePlayerButton.hidden = false;

    if (!selectedPlayer) {
      openPlayerDialog(false);
    }
  } catch (error) {
    console.error(error);

    loading.classList.add("error");

    loading.textContent =
      `Fehler beim Laden: ${error.message}`;
  }
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker
    .register(
      "service-worker.js",
      {
        updateViaCache: "none"
      }
    )
    .then(
      registration =>
        registration.update()
    )
    .catch(error => {
      console.error(
        "Service Worker konnte nicht registriert werden:",
        error
      );
    });
}

loadData();

window.addEventListener("online", updateConnectionStatus);
window.addEventListener("offline", updateConnectionStatus);
