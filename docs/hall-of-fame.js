function buildHallOfFame(seasons) {
  const players = new Map();
  const streaks = [];
  const ordered = [...seasons].sort((a, b) => a.id.localeCompare(b.id));
  for (const season of ordered) {
    for (const row of season.rows) {
      if (!players.has(row.name)) players.set(row.name, { name: row.name, points: 0, missing: false, seasons: [], podium: [], community: 0, tippspiel: 0, managerspiel: 0 });
      const player = players.get(row.name);
      player.seasons.push(season);
      if (row.eternal === null) player.missing = true;
      else player.points += row.eternal;
      for (const mode of ['community', 'tippspiel', 'managerspiel']) if (row[mode].rank === 1) player[mode]++;
      if (row.community.rank !== null && row.community.rank <= 3) player.podium.push(season);
    }
  }
  for (const player of players.values()) {
    let run = [];
    for (const season of ordered) {
      const winner = season.rows.some(row => row.name === player.name && row.community.rank === 1);
      if (winner) {
        if (run.length && Number(season.id.slice(0, 4)) !== Number(run.at(-1).id.slice(0, 4)) + 1) { streaks.push({ name: player.name, seasons: run }); run = []; }
        run.push(season);
      } else if (run.length) { streaks.push({ name: player.name, seasons: run }); run = []; }
    }
    if (run.length) streaks.push({ name: player.name, seasons: run });
    player.average = player.missing ? null : player.points / player.seasons.length;
  }
  return { players: [...players.values()], streaks };
}

if (typeof module !== 'undefined') module.exports = { buildHallOfFame };
if (typeof document !== 'undefined') (() => {
  const seasons = window.TASMANIA_ARCHIVE || [];
  const { players, streaks } = buildHallOfFame(seasons);
  let metric = 'points';
  let titleSort = 'community';
  const modes = [...document.querySelectorAll('[data-fame-mode]')];
  const sorts = [...document.querySelectorAll('[data-title-sort]')];
  const labels = { community: 'Gesamt', tippspiel: 'Tipp', managerspiel: 'Manager' };
  const el = (tag, text, className) => { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (className) node.className = className; return node; };
  const ownName = () => { try { return selectedPlayer || localStorage.getItem(PLAYER_STORAGE_KEY); } catch (_) { return selectedPlayer; } };
  function nameCell(player) {
    const cell = el('td'); cell.append(el('strong', player.name));
    if (player.name === ownName()) cell.append(el('span', 'Du', 'you-badge'));
    return cell;
  }
  function render() {
    const body = document.getElementById('fame-eternal-rows'); body.replaceChildren();
    const rows = [...players].sort((a, b) => (b[metric] ?? -Infinity) - (a[metric] ?? -Infinity) || a.name.localeCompare(b.name, 'de'));
    let rank = 0;
    rows.forEach((player, index) => {
      if (!index || player[metric] !== rows[index - 1][metric]) rank = index + 1;
      const tr = el('tr'); if (player.name === ownName()) tr.className = 'archive-is-me';
      const place = el('td'); place.append(el('span', String(rank), `rank-badge ${getRankClass(rank)}`));
      const name = nameCell(player); name.append(el('small', `${player.seasons.length} Saisons`, 'archive-row-note'));
      const value = player[metric];
      tr.append(place, name, el('td', value === null ? '–' : value.toLocaleString('de-DE', { minimumFractionDigits: metric === 'average' ? 2 : 0, maximumFractionDigits: metric === 'average' ? 2 : 0 })));
      body.append(tr);
    });
    document.getElementById('fame-value-label').textContent = metric === 'average' ? 'Ø Punkte' : 'Punkte';
    modes.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.fameMode === metric)));
    const titles = document.getElementById('fame-title-rows'); titles.replaceChildren();
    [...players].sort((a, b) => b[titleSort] - a[titleSort] || a.name.localeCompare(b.name, 'de')).forEach(player => {
      const row = el('tr'); if (player.name === ownName()) row.className = 'archive-is-me';
      row.append(nameCell(player), ...Object.keys(labels).map(key => el('td', String(player[key])))); titles.append(row);
    });
    sorts.forEach(button => { const active = button.dataset.titleSort === titleSort; button.textContent = labels[button.dataset.titleSort] + (active ? ' ↓' : ''); button.parentElement.setAttribute('aria-sort', active ? 'descending' : 'none'); });
    document.getElementById('fame-sort-status').textContent = `Sortiert nach ${ { community: 'Gesamttiteln', tippspiel: 'Tippspieltiteln', managerspiel: 'Managerspieltiteln' }[titleSort]}`;
  }
  function record(title, value, entries, detail) {
    const card = el('article', undefined, 'fame-record'); card.append(el('h4', title), el('strong', value), el('p', detail));
    const disclosure = el('details'); disclosure.append(el('summary', 'Spielzeiten ansehen'));
    for (const entry of entries) disclosure.append(el('p', `${entry.name}: ${entry.seasons.map(season => season.label).join(', ')}`));
    card.append(disclosure); document.getElementById('fame-records').append(card);
  }
  if (seasons.length) document.getElementById('fame-period').textContent = `${seasons[0].label} bis ${seasons.at(-1).label} · ${seasons.length} dokumentierte Spielzeiten`;
  const longest = Math.max(0, ...streaks.map(run => run.seasons.length));
  const runs = streaks.filter(run => run.seasons.length === longest);
  record('Längste Meisterserie', `${longest} Gesamtsiege in Folge`, runs, [...new Set(runs.map(run => run.name))].join(' & '));
  const podium = Math.max(0, ...players.map(player => player.podium.length));
  const podiumLeaders = players.filter(player => player.podium.length === podium);
  record('Am häufigsten auf dem Podium', `${podium} Top-3-Platzierungen`, podiumLeaders.map(player => ({ name: player.name, seasons: player.podium })), podiumLeaders.map(player => player.name).join(' & ') + ' · Gesamtwertung');
  window.addEventListener('tasmania-player-change', render);
  modes.forEach(button => button.addEventListener('click', () => { metric = button.dataset.fameMode; render(); }));
  sorts.forEach(button => button.addEventListener('click', () => { titleSort = button.dataset.titleSort; render(); }));
  document.getElementById('open-fame-button').addEventListener('click', () => { render(); setAppArea('fame'); });
  render();
})();
