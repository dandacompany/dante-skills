// 롯데하이마트 — POST /app/goods/reviewAllListAjax (HTML 조각). 첫 화면용 reviewListInitAjax 는 3개만 주고
// 페이지가 넘지 않으니 쓰지 않는다. 2026-10-21 실측 6/6.
async (opts) => {
  const goodsNo = new URLSearchParams(location.search).get("goodsNo");
  if (!goodsNo) throw new Error("STRUCTURE: goodsNo 를 URL 에서 찾지 못함");
  const totalEl = await scrollUntil(
    () => document.querySelector("#gdasCnt"),
    6,
  );
  const total = totalEl ? +totalEl.value || null : null;
  const res = await paginate(async (p) => {
    const d = html(
      await req("/app/goods/reviewAllListAjax", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          "X-Requested-With": "XMLHttpRequest",
        },
        body: `goodsNo=${goodsNo}&goodsCmpsCd=01&reviewType=&orderType=02&page=${p}&starPoint=&selectedGoodsNo=&goodsStatSctCd=01`,
      }),
    );
    const items = [...d.querySelectorAll("li.hm-list__item")]
      .filter((l) => /\d{4}\.\d{2}\.\d{2}/.test(l.innerText || l.textContent))
      .map((l) => {
        const t = txt(l);
        const m = t.match(
          /^(\d)\d?\s+(\S+)\s+(\d{4}\.\d{2}\.\d{2})\s+(.*?)(?:\s+\d+\s+신고하기)?$/,
        );
        return {
          review_id: "",
          created_at: m ? m[3].replace(/\./g, "-") : "",
          rating: m ? +m[1] : "",
          writer: m?.[2] || "",
          option: "",
          title: "",
          content: m?.[4] || t,
          survey: "",
          helpful: "",
          photo_count: l.querySelectorAll("img").length,
          photo_urls: "",
        };
      });
    if (p === 1 && total && !items.length)
      throw new Error("STRUCTURE: 건수는 있는데 li.hm-list__item 이 없음");
    return { total, items };
  }, opts);
  return {
    platform: "himart",
    product_id: goodsNo,
    product_name: document.title.replace(/^롯데하이마트\s*\|\s*/, ""),
    ...res,
  };
};
