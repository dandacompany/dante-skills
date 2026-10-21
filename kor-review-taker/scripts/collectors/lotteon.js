// 롯데ON — POST https://pbf.lotteon.com/review/v1/productDetail/getProductReviewSearchList (JSON, 다른 출처지만
// 페이지가 credentials 포함으로 부르는 것과 같다). sitmNoList 의 단품번호는 상품 페이지 HTML 의 `LO{상품}_{단품}`.
// 회원번호(mbNo 등)는 옮기지 않는다. trNo 는 비워도 된다. 2026-10-22 실측 71/71.
async (opts) => {
  const pd = location.pathname.match(/LO\d+/)?.[0];
  if (!pd) throw new Error("STRUCTURE: 상품번호(LO…)를 URL 에서 찾지 못함");
  const sitm = (document.documentElement.innerHTML.match(
    new RegExp(pd + "_\\d+"),
  ) || [])[0];
  if (!sitm)
    throw new Error("STRUCTURE: 페이지에서 sitmNo(" + pd + "_…)를 찾지 못함");
  const res = await paginate(async (p) => {
    const j = await req(
      "https://pbf.lotteon.com/review/v1/productDetail/getProductReviewSearchList",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sitmNoList: [sitm],
          mallNo: "1",
          searchKeyword: "",
          synList: [],
          ctntDpYn: "",
          repurchaseRvYn: "",
          afflSqncTypCdDnDvYn: "",
          pdStfdVal: "",
          custAdtnArtl: [],
          itmOpt: [],
          sort: "RANK",
          pageNo: p,
          rowsPerPage: 20,
          onlySellerRvYn: "N",
          trNo: "",
          rvNoList: [],
        }),
      },
      "json",
    );
    const rl = j?.data?.reviewList;
    if (!Array.isArray(rl?.dataList))
      throw new Error("STRUCTURE: data.reviewList.dataList 없음");
    return {
      total: rl.totalCount,
      items: rl.dataList.map((x) => ({
        review_id: x.rvNo,
        created_at: x.regDttm,
        rating: x.pdStfdVal,
        writer: "",
        option: x.itmNm && x.itmNm !== "단일상품" ? x.itmNm : "",
        title: "",
        content: x.rvCnts,
        survey: (x.evaArtlJsn || [])
          .map((a) =>
            [a.evaArtlNm || a.nm, a.evaArtlVal || a.val]
              .filter(Boolean)
              .join(": "),
          )
          .join(" / "),
        helpful: x.rvRcNbr ?? "",
        photo_count: x.rvDvsCd === "PHTO" ? 1 : 0,
        photo_urls: "",
      })),
    };
  }, opts);
  return {
    platform: "lotteon",
    product_id: pd,
    product_name: document.title.replace(/^\[[^\]]*\]|\s*:\s*롯데ON\s*$/g, ""),
    ...res,
  };
};
