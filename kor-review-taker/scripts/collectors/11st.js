// 11번가 — GET /products/{id}/review-list (HTML 조각). 리뷰 iframe(review-frame) 안에서 부르므로
// 메인 프레임 캡처에 안 잡힌다. iframe 이 실제로 부른 URL 의 쿼리를 그대로 쓰고 pageNo/pageSize 만 바꾼다.
// 2026-10-21 실측 4/4.
async (opts) => {
  const pid = location.pathname.match(/products\/(?:pa\/)?(\d+)/)?.[1];
  if (!pid) throw new Error("STRUCTURE: 상품번호를 URL 에서 찾지 못함");
  const seen = await scrollUntil(
    () =>
      resourceUrls().find((u) =>
        /^\/products\/\d+\/review-list$/.test(new URL(u).pathname),
      ),
    8,
  );
  const base = new URL(
    seen ||
      `${location.origin}/products/${pid}/review-list?myProduct=false&pntVals=&rtype=&sortType=01&themeNm=&optNm=&kkukNo=0&marketType=RETAIL`,
  );
  base.searchParams.set("pageSize", "20");
  const res = await paginate(async (p) => {
    base.searchParams.set("pageNo", String(p));
    const d = html(await req(base.toString()));
    const total =
      +txt(d.querySelector(".c_product_title .sub i")).replace(/\D/g, "") ||
      null;
    const items = [...d.querySelectorAll("li.review_list_element")].map((l) => {
      const q = (s) => l.querySelector(s);
      return {
        review_id: l.dataset.contmapno,
        created_at: (txt(q(".date")) || txt(q("[class*=date]"))).replace(
          /\./g,
          "-",
        ),
        rating: +txt(q(".grade em")) || "",
        writer: q(".name")?.dataset.nick || txt(q(".name")),
        option: txt(q(".option dd")),
        title: "",
        content: txt(q(".cont_review_hide") || q(".cont_text_wrap")),
        survey: [...l.querySelectorAll(".value dt")]
          .map((dt) => `${txt(dt)}: ${txt(dt.nextElementSibling)}`)
          .join(" / "),
        helpful: "",
        photo_count: l.querySelectorAll(".c_product_review_thumbnail2 li")
          .length,
        photo_urls: "",
      };
    });
    if (p === 1 && total && !items.length)
      throw new Error(
        "STRUCTURE: 건수는 있는데 li.review_list_element 가 없음",
      );
    return { total, items };
  }, opts);
  return {
    platform: "11st",
    product_id: pid,
    product_name: document.title.replace(/\s*-\s*11번가\s*$/, ""),
    ...res,
  };
};
