use reqwest::Client;

const BANGUMI_API_BASE: &str = "https://api.bgm.tv";
const USER_AGENT: &str = "rinshankaiho.fun (https://github.com/hexsix/bgm-rank-api)";

pub struct BangumiClient {
    pub(super) client: Client,
    pub(super) base_url: String,
    pub(super) ua: String,
}

impl BangumiClient {
    pub fn new() -> Self {
        Self {
            client: Client::new(),
            base_url: BANGUMI_API_BASE.to_string(),
            ua: USER_AGENT.to_string(),
        }
    }
}

impl Default for BangumiClient {
    fn default() -> Self {
        Self::new()
    }
}
