// 크랙 스토리챗 웹 쇼케이스 캐릭터 도감 스크립트
// characters 배열은 deploy.py가 프로젝트 characters.md로부터 추출하여 주입하거나 아래 기본값을 사용합니다.

const characters = window.CHARACTERS_DATA || [
  { id: "01", name: "에리카 아르덴", group: "student", type: "기사학부 · 1학년", role: "깐깐한 정석파 라이벌", quote: "기본을 무시한 검술은 검술이 아니야." },
  { id: "02", name: "테오 아르덴", group: "student", type: "기사학부 · 1학년", role: "호쾌한 전투광", quote: "생각은 나중에. 일단 붙자." },
  { id: "03", name: "셀리아 아르덴", group: "student", type: "기사학부 · 4학년", role: "차가운 완벽주의 선배", quote: "다시. 아직 부족해." },
  { id: "04", name: "엘리아 벨로아", group: "student", type: "마법학부 · 1학년", role: "나른한 마법 오타쿠", quote: "잠깐. 그 술식 다시 보여줘." }
];

const grid = document.querySelector("#character-grid");
const statCharacters = document.querySelector("#stat-characters");

if (statCharacters) {
  statCharacters.textContent = characters.length;
}

if (grid) {
  for (const character of characters) {
    const card = document.createElement("article");
    card.className = "character-card";
    card.dataset.group = character.group || "all";
    const imageRevision = character.revision ? `?v=${character.revision}` : "";
    // 기본 일반 표정(a01.webp) 또는 썸네일(s01.webp) 렌더링
    const imgSrc = character.img || `/${character.id}/a01.webp`;
    card.innerHTML = `
      <img src="${imgSrc}${imageRevision}" alt="${character.name}" loading="lazy" width="832" height="1216" onerror="this.onerror=null; this.src='/${character.id}/01.webp';">
      <div class="character-overlay">
        <span class="character-number">${character.id}</span>
        <span class="character-type">${character.type || "주요 인물"}</span>
        <h3>${character.name}</h3>
        <p class="character-role">${character.role || ""}</p>
        ${character.quote ? `<p class="character-quote">“${character.quote}”</p>` : ""}
      </div>`;
    grid.append(card);
  }
}

document.querySelectorAll("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const filter = button.dataset.filter;
    document.querySelectorAll("[data-filter]").forEach((item) => item.classList.toggle("active", item === button));
    document.querySelectorAll(".character-card").forEach((card) => {
      card.classList.toggle("hidden", filter !== "all" && card.dataset.group !== filter);
    });
  });
});
