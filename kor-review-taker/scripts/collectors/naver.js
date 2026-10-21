// 네이버 스마트스토어·브랜드스토어 — POST {prefix}/v1/contents/reviews/query-pages (JSON).
// originProductNo·checkoutMerchantNo 는 화면 상품번호와 다르다. 페이지가 부르는 product-summary 요청 URL 에서 읽는다.
// x-client-rtk 등 봇 방지 헤더 없이도 같은 탭 fetch 는 응답한다(2026-10-21 실측 19/19). 토큰을 꺼내 쓰지 않는다.
async (opts) => {
  const find = () =>
    resourceUrls().find((u) =>
      /\/v1\/contents\/reviews\/product-summary\/\d+\?.*checkoutMerchantNo=\d+/.test(
        u,
      ),
    );
  const u = await scrollUntil(find);
  if (!u)
    throw new Error(
      "STRUCTURE: product-summary 요청이 보이지 않음(originProductNo/checkoutMerchantNo 미확보)",
    );
  const url = new URL(u);
  const prefix = url.pathname.split("/v1/")[0];
  const originProductNo = +url.pathname.match(/product-summary\/(\d+)/)[1];
  const checkoutMerchantNo = +url.searchParams.get("checkoutMerchantNo");
  const res = await paginate(async (p) => {
    const j = await req(
      `${url.origin}${prefix}/v1/contents/reviews/query-pages`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json, text/plain, */*",
        },
        body: JSON.stringify({
          checkoutMerchantNo,
          originProductNo,
          page: p,
          pageSize: 20,
          reviewSearchSortType: "REVIEW_CREATE_DATE_DESC",
        }),
      },
      "json",
    );
    if (!Array.isArray(j?.contents))
      throw new Error("STRUCTURE: contents 배열 없음");
    return {
      total: j.totalElements,
      items: j.contents.map((c) => ({
        review_id: c.id,
        created_at: c.createDate,
        rating: c.reviewScore,
        writer: c.maskedWriterId,
        option: c.productOptionContent || "",
        title: "",
        content: c.reviewContent,
        survey: "",
        helpful: c.helpCount ?? "",
        photo_count: (c.reviewAttaches || []).length,
        photo_urls: (c.reviewAttaches || []).map((a) => a.attachUrl).join(" "),
      })),
    };
  }, opts);
  return {
    platform: "naver",
    product_id: location.pathname.match(/products\/(\d+)/)?.[1],
    product_name: document.title.split(" : ")[0],
    ...res,
  };
};
