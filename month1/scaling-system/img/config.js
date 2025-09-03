const isProd = true;

const Config = {
    BASE_URL: isProd
        // ? "https://tmstest.bracbank.com/api/apiconnector"
        ? "https://msfleet.metalstudio.com.bd/api/apiconnector"
        : "http://127.0.0.1:8000/api/apiconnector",
    DEBUG_MODE: !isProd,
    TOKEN_STORAGE_KEY: "access_token"
};
