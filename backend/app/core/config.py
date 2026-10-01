from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://127.0.0.1:27017"
    mongodb_database: str = "koperasi_db"

    # WAJIB diganti di production (lihat .env.example).
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 480

    # Origin frontend yang diizinkan (dipisah koma).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Rate limit login: maksimal N percobaan gagal per jendela waktu
    # untuk kombinasi (IP, username).
    login_max_attempts: int = 5
    login_window_seconds: int = 300

    # Metode HPP untuk laporan laba. Saat ini hanya satu metode yang
    # diimplementasikan: harga beli produk yang di-snapshot saat
    # transaksi penjualan terjadi.
    cogs_method: str = "SNAPSHOT_PURCHASE_PRICE"

    # Zona waktu bisnis: dipakai untuk penomoran dokumen harian
    # (TRX-YYYYMMDD-NNNN) dan batas "hari ini" pada dashboard/laporan.
    app_timezone: str = "Asia/Jakarta"

    # Transaksi multi-dokumen MongoDB hanya tersedia di replica set /
    # sharded cluster. "auto" = deteksi saat startup; "off" = selalu pakai
    # mekanisme kompensasi (rollback manual); "on" = paksa transaksi.
    mongodb_transactions: str = "auto"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
