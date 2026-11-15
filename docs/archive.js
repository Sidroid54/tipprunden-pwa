/* Season archive uses the same reviewed source as the historical master. */
(() => {
  const seasons = window.TASMANIA_ARCHIVE || [];
  const picker = document.getElementById('archive-season');
  const previous = document.getElementById('archive-previous');
  const next = document.getElementById('archive-next');
  const modes = [...document.querySelectorAll('[data-archive-mode]')];
  const labels = { community: 'Gesamtwertung', tippspiel: 'Tippspiel', managerspiel: 'Managerspiel' };
  const storageKey = 'tasmania-archive-season';
  let saved;
  try { saved = localStorage.getItem(storageKey); } catch (_) { /* Storage may be unavailable. */ }
  let index = Math.max(0, seasons.findIndex(season => season.id === saved));
  if (!saved || !seasons.some(season => season.id === saved)) index = seasons.length - 1;
  let mode = 'community';
  const element = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  seasons.slice().reverse().forEach(season => {
    const option = element('option', season.label);
    option.value = season.id;
    picker.append(option);
  });

  function render() {
    const season = seasons[index];
    if (!season) return;
    picker.value = season.id;
    previous.disabled = index === 0;
    next.disabled = index === seasons.length - 1;
    try { localStorage.setItem(storageKey, season.id); } catch (_) { /* In-memory selection still works. */ }
    const premier = season.id === '2002-03';
    document.getElementById('archive-winners-title').textContent = `Die Sieger ${season.label}`;
    const winners = document.getElementById('archive-winners');
    winners.replaceChildren();
    for (const [key, label] of Object.entries(labels)) {
      const names = season.rows.filter(row => row[key].rank === 1).map(row => row.name);
      const group = element('div');
      group.append(element('dt', label), element('dd', names.join(' & ') || (premier ? 'Nicht ausgetragen' : 'Nicht überliefert')));
      winners.append(group);
    }
    modes.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.archiveMode === mode)));
    document.getElementById('archive-table-title').textContent = `${labels[mode]} · Endstand ${season.label}`;
    const rows = season.rows.filter(row => row[mode].rank !== null || row[mode].points !== null)
      .sort((a, b) => (a[mode].rank ?? Infinity) - (b[mode].rank ?? Infinity) || a.name.localeCompare(b.name, 'de'));
    const empty = document.getElementById('archive-empty');
    empty.hidden = rows.length > 0;
    empty.textContent = premier && mode !== 'managerspiel'
      ? 'In der ersten überlieferten Saison wurde nur das Managerspiel ausgetragen. Ein Tippspiel und eine kombinierte Gesamtwertung gab es noch nicht.'
      : 'Für diesen Wettbewerb liegt noch keine Endtabelle vor.';
    document.getElementById('archive-table').hidden = !rows.length;
    const showEternal = mode === 'community' || (premier && mode === 'managerspiel');
    document.getElementById('archive-eternal').hidden = !showEternal || !rows.length;
    document.getElementById('archive-eternal-basis').textContent = premier
      ? '2002/03 dient die Managerspiel-Endwertung als Grundlage für die Ewige Tabelle.'
      : 'Grundlage ist der Rang in der Gesamtwertung. Ein Strich bedeutet: kein einzelner Saisonwert überliefert.';
    const body = document.getElementById('archive-rows');
    body.replaceChildren();
    let ownName = selectedPlayer;
    try { ownName = ownName || localStorage.getItem(PLAYER_STORAGE_KEY); } catch (_) { /* Optional highlighting. */ }
    for (const row of rows) {
      const value = row[mode];
      const tr = element('tr');
      if (row.name === ownName) tr.classList.add('archive-is-me');
      const rank = element('td');
      rank.append(element('span', value.rank ?? '–', `rank-badge ${getRankClass(value.rank)}`));
      const name = element('td');
      name.append(element('strong', row.name));
      if (row.name === ownName) name.append(element('span', 'Du', 'you-badge'));
      if (value.rank !== null && rows.filter(other => other[mode].rank === value.rank).length > 1) {
        name.append(element('small', 'Geteilter Rang', 'archive-row-note'));
      }
      if (showEternal) name.append(element('small', row.eternal === null ? 'Ewige Tabelle: –' : `+${row.eternal} Ewige Tabelle`, 'archive-row-note'));
      const points = element('td', value.points === null ? '–' : value.points.toLocaleString('de-DE'));
      if (value.note) {
        const details = element('details', undefined, 'archive-review');
        details.append(element('summary', 'Noch in Prüfung'), element('p', value.note));
        name.append(details);
      }
      tr.append(rank, name, points);
      body.append(tr);
    }
  }
  picker.addEventListener('change', () => {
    index = seasons.findIndex(season => season.id === picker.value);
    render();
  });
  previous.addEventListener('click', () => { if (index > 0) { index--; render(); } });
  next.addEventListener('click', () => { if (index < seasons.length - 1) { index++; render(); } });
  modes.forEach(button => button.addEventListener('click', () => { mode = button.dataset.archiveMode; render(); }));
  document.getElementById('open-archive-button').addEventListener('click', () => { render(); setAppArea('archive'); });
  render();
})();
