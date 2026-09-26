# Подписка через домен-фронтинг

Домен-фронтинг (Domain Fronting) позволяет обращаться к серверу подписки через «фронт» — крупный CDN/облачный домен, который не блокируется. Соединение устанавливается с IP-адресом фронта, но HTTP-запрос идёт с Host-заголовком настоящего сервера. Провайдер видит подключение к «белому» домену, а не к домену VPN-панели.

## Формат ссылки

Фронтинг-параметры передаются в фрагменте ссылки подписки (после `#имя?`):

```text
https://<front-domain>/<path>/<token>#<name>?resolve-address=<front-domain>&host=<real-host>
```

| Часть | Значение | Пример |
| --- | --- | --- |
| `<front-domain>` | Домен-фронт в самой ссылке (authority) — виден провайдеру как цель подключения | `gmail.com` |
| `resolve-address` | Домен, который клиент резолвит и подключается по IP напрямую (обычно тот же фронт) | `gmail.com` |
| `host` | Настоящий Host-заголовок — домен, на который CDN маршрутизирует запрос | `storage.googleapis.com` |

`resolve-address` и `host` можно комбинировать с любым `front-domain`: адрес подключения определяется фронт-доменом (`resolve-address`), а маршрутизация на сервер — заголовком `host`.

## Пример: три зеркала

Первый URL без метки, последующие — с метками `url:N=`, в конце `fallback-url=`:

```text
https://gmail.com/runrun1/token#rahima?resolve-address=gmail.com&host=storage.googleapis.com|url:1=https://www.google.com/runrun1/token#rahima?resolve-address=www.google.com&host=storage.googleapis.com|url:2=https://fcm.googleapis.com/runrun1/token#rahima?resolve-address=fcm.googleapis.com&host=storage.googleapis.com|fallback-url=https://backup.example.com/token
```

Клиент пробует зеркала по порядку: `gmail.com` → `www.google.com` → `fcm.googleapis.com`. Каждый резолвится отдельно, соединение идёт на IP соответствующего фронта, Host-заголовок всегда `storage.googleapis.com`. Если все три недоступны — используется `fallback-url`. Тот же список без меток (просто через `|`) тоже работает.

## Управление фронтинг-зеркалами из подписки

Команды управления ([app-management.md](app-management.md)) работают с фронтинг-зеркалами через помеченные позиции: первый URL — позиция `0`, `url:1` — второй, `url:N` — позиция `N`:

```http
new-url: https://drive.google.com/runrun1/token#rahima?resolve-address=drive.google.com&host=storage.googleapis.com
new-url-1: https://www.google.com/runrun1/token#rahima?resolve-address=www.google.com&host=storage.googleapis.com
new-url-1: resolve-address=142.251.41.165
new-url-1: host=storage.googleapis.com
new-domain: drive.google.com
new-url-2: 0
fallback-url: https://fcm.googleapis.com/runrun1/token#rahima?resolve-address=fcm.googleapis.com&host=storage.googleapis.com
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
