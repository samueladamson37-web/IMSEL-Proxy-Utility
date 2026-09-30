# Подписка через домен-фронтинг

Домен-фронтинг (Domain Fronting) позволяет обращаться к серверу подписки через «фронт» — крупный CDN/облачный домен, который не блокируется. Соединение устанавливается с IP-адресом фронта, но HTTP-запрос идёт с Host-заголовком настоящего сервера. Провайдер видит подключение к «белому» домену, а не к домену VPN-панели.

## Формат ссылки

Фронтинг-параметры передаются в фрагменте ссылки подписки (после `#имя?`):

```text
https://<front-domain>/<path>/<token>#<name>?resolve-address=<front-domain>&host=<real-host>
```

| Часть | Значение | Пример |
| --- | --- | --- |
| `<front-domain>` | Домен-фронт в самой ссылке (authority) — виден провайдеру как цель подключения | `cdn.imsel.dev` |
| `resolve-address` | Домен, который клиент резолвит и подключается по IP напрямую (обычно тот же фронт) | `cdn.imsel.dev` |
| `host` | Настоящий Host-заголовок — домен, на который CDN маршрутизирует запрос | `backend.imsel-api.com` |

`resolve-address` и `host` можно комбинировать с любым `front-domain`: адрес подключения определяется фронт-доменом (`resolve-address`), а маршрутизация на сервер — заголовком `host`.

## Пример: три зеркала

Первый URL без метки, последующие — с метками `url:N=`, в конце `fallback-url=`:

```text
https://cdn.imsel.dev/subpath/token#MySub?resolve-address=cdn.imsel.dev&host=backend.imsel-api.com|url:1=https://fallback.imsel.dev/subpath/token#MySub?resolve-address=fallback.imsel.dev&host=backend.imsel-api.com|url:2=https://route.imsel.dev/subpath/token#MySub?resolve-address=route.imsel.dev&host=backend.imsel-api.com|fallback-url=https://backup.imsel.dev/token
```

Клиент пробует зеркала по порядку: `cdn.imsel.dev` → `fallback.imsel.dev` → `route.imsel.dev`. Каждый резолвится отдельно, соединение идёт на IP соответствующего фронта, Host-заголовок всегда `backend.imsel-api.com`. Если все три недоступны — используется `fallback-url`. Тот же список без меток (просто через `|`) тоже работает.

## Управление фронтинг-зеркалами из подписки

Команды управления ([app-management.md](app-management.md)) работают с фронтинг-зеркалами через помеченные позиции: первый URL — позиция `0`, `url:1` — второй, `url:N` — позиция `N`:

```http
new-url: https://mirror.imsel.dev/subpath/token#MySub?resolve-address=mirror.imsel.dev&host=backend.imsel-api.com
new-url-1: https://fallback.imsel.dev/subpath/token#MySub?resolve-address=fallback.imsel.dev&host=backend.imsel-api.com
new-url-1: resolve-address=198.51.100.15
new-url-1: host=backend.imsel-api.com
new-domain: mirror.imsel.dev
new-url-2: 0
fallback-url: https://route.imsel.dev/subpath/token#MySub?resolve-address=route.imsel.dev&host=backend.imsel-api.com
```

- `new-url` — заменить **только первый URL** (позиция 0);
- `new-url-N: <url>` — заменить зеркало на позиции N целиком (обычный или фронтинг-URL); N = количество — добавить в конец; `0` — удалить;
- `new-url-N: resolve-address=<домен|IP>` — точечно заменить только `resolve-address` (IP-адрес разрешён: фронт резолвится заранее и подключение идёт на указанный IP);
- `new-url-N: host=<домен>` — точечно заменить только `host` (Host-заголовок фронтинга);
- `new-domain` / `new-domain-N` — заменить фронт-домен: меняется host ссылки и `resolve-address` (если совпадал со старим фронтом); `host=` не трогается — CDN-маршрутизация сохраняется;
- `fallback-url` — запасной фронтинг-URL на случай, когда все зеркала недоступны.

## Ограничения

- Резолв `resolve-address` выполняется системным DNS: если домен фронта резолвится на «заглушку», соединение не состоится — выбирайте живые фронты.
- Фронт должен поддерживать маршрутизацию по Host-заголовку на ваш сервер (типично для Google/Cloudflare/AWS-инфраструктур); иначе CDN вернёт ошибку.
- HTTP/2-мультиплексирование на некоторых CDN игнорирует Host-заголовок после установления соединения — при странном поведении попробуйте другой фронт.
