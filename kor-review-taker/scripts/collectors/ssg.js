// SSG.COM — GET /item/ajaxItemCommentList.ssg (HTML 조각). 항목은 div.rvw_expansion_panel[data-postngid].
// 조각 안 JSON-LD 는 본문 제어문자 때문에 JSON.parse 가 깨지니 DOM 을 읽는다.
// 연속 요청 중 빈 응답이 섞인다(소프트 스로틀링) — paginate 의 재시도가 받아 준다. 2026-10-22 실측 199/199.
async (opts) => {
  const sp = new URLSearchParams(location.search);
  const itemId = sp.get("itemId");
  const siteNo = sp.get("siteNo") || "6004";
  if (!itemId) throw new Error("STRUCTURE: itemId 를 URL 에서 찾지 못함");
  const m = (document.body.innerText || "").match(
    /고객리뷰\s*\(\s*([\d,]+)\s*건/,
  );
  const total = m ? +m[1].replace(/,/g, "") : null;
  const res = await paginate(async (p) => {
    const d = html(
      await req(
        `/item/ajaxItemCommentList.ssg?itemId=${itemId}&siteNo=${siteNo}&filterCol=10&sortCol=&uitemId=&recomAttrGrpId=&recomAttrId=&page=${p}&pageSize=10&oreItemId=&oreItemReviewYn=N&nlpEntyId=`,
      ),
    );
    const items = [
      ...d.querySelectorAll("div.rvw_expansion_panel[data-postngid]"),
    ].map((e) => {
      const q = (s) => e.querySelector(s);
      const imgs = [...e.querySelectorAll(".rvw_item_thumb_group img")];
      return {
        review_id: e.dataset.postngid,
        created_at: ((e.textContent || "").match(/20\d\d[.-]\d\d[.-]\d\d/) || [
          "",
        ])[0].replace(/\./g, "-"),
        rating: +txt(q(".cdtl_star_on em")) || "",
        writer: txt(q(".rvw_item_user_id")),
        option: "",
        title: "",
        content: txt(q(".rvw_item_text")),
        survey: "",
        helpful: "",
        photo_count: imgs.length,
        photo_urls: imgs
          .map((i) => new URL(i.getAttribute("src"), location.href).href)
          .join(" "),
      };
    });
    return { total, items };
  }, opts);
  return {
    platform: "ssg",
    product_id: itemId,
    product_name: document.title.replace(/\s*-\s*SSG\.COM\s*$/, ""),
    ...res,
  };
};
