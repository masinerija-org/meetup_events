/* ---- Router ---- */

function getRoute() {
    const hash = window.location.hash.slice(1) || "/";
    if (hash === "/" || hash === "") return { page: "home" };
    const m = hash.match(/^\/event\/(\w+)$/);
    if (m) return { page: "event", eventId: m[1] };
    return { page: "home" };
}

function route() {
    const { page, eventId } = getRoute();
    if (page === "event") {
        renderEvent(eventId);
    } else {
        renderHome();
    }
}

/* ---- Helpers ---- */

function formatDate(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function getInitials(name) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
}

const AVATAR_COLORS = [
    "#e94560", "#0f3460", "#16213e", "#533483",
    "#2b9348", "#d62828", "#457b9d", "#6a4c93",
];

function avatarColor(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

function escapeHtml(text) {
    const el = document.createElement("span");
    el.textContent = text;
    return el.innerHTML;
}

/* ---- Renderers ---- */

function renderHome() {
    const g = SITE_DATA.group;
    const app = document.getElementById("app");
    app.innerHTML =
        renderHero(g) +
        renderEventsGallery(SITE_DATA.events) +
        renderAdministrators(g.administrators) +
        renderFooter();
}

function renderEvent(eventId) {
    const ev = SITE_DATA.events.find((e) => e.event_id === eventId);
    if (!ev) {
        renderHome();
        return;
    }
    const app = document.getElementById("app");
    app.innerHTML =
        renderEventHero(ev) +
        renderEventDetail(ev) +
        renderFooter();
    window.scrollTo(0, 0);
}

/* ---- Component renderers ---- */

function renderHero(group) {
    return `
    <section class="hero" style="background-image:url('${group.cover_image}')">
        <h1>${escapeHtml(group.name)}</h1>
        <p>${escapeHtml(group.description)}</p>
    </section>`;
}

function renderEventsGallery(events) {
    const cards = events
        .map(
            (ev) => `
        <a class="event-card" href="#/event/${ev.event_id}">
            <img src="${ev.cover_image || "images/group_cover.jpeg"}"
                 alt="${escapeHtml(ev.title)}"
                 loading="lazy">
            <div class="event-card-body">
                <div class="event-card-title">${escapeHtml(ev.title)}</div>
                <div class="event-card-meta">
                    <span>${ev.going_count} attendees</span>
                </div>
            </div>
        </a>`
        )
        .join("");

    return `
    <section class="section">
        <h2 class="section-title">Events</h2>
        <div class="events-grid">${cards}</div>
    </section>`;
}

function renderAdministrators(admins) {
    const cards = admins
        .map(
            (a) => `
        <div class="admin-card">
            <div class="admin-avatar" style="background:${avatarColor(a.name)}">
                ${getInitials(a.name)}
            </div>
            <div class="admin-name">${escapeHtml(a.name)}</div>
        </div>`
        )
        .join("");

    return `
    <section class="section">
        <h2 class="section-title">Group Administrators</h2>
        <div class="admins-grid">${cards}</div>
    </section>`;
}

function renderEventHero(ev) {
    return `
    <section class="hero" style="background-image:url('${ev.cover_image || "images/group_cover.jpeg"}')">
        <h1>${escapeHtml(ev.title)}</h1>
    </section>`;
}

function renderEventDetail(ev) {
    const meta = [];
    if (ev.venue_name) meta.push(`<li><strong>Venue:</strong> ${escapeHtml(ev.venue_name)}</li>`);
    if (ev.venue_city) meta.push(`<li><strong>City:</strong> ${escapeHtml(ev.venue_city)}</li>`);
    meta.push(`<li><strong>Date:</strong> ${formatDate(ev.date_time)}</li>`);
    meta.push(`<li><strong>Attendees:</strong> ${ev.going_count}</li>`);

    return `
    <div class="event-detail">
        <h2>${escapeHtml(ev.title)}</h2>
        <ul class="event-meta-list">${meta.join("")}</ul>
        <div class="event-description">${ev.description}</div>
        <a class="btn-back" href="#/">Back</a>
    </div>`;
}

function renderFooter() {
    return `<footer class="footer">&copy; ${new Date().getFullYear()} Machinery</footer>`;
}

/* ---- Init ---- */

window.addEventListener("hashchange", route);
route();