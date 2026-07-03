import CHANNEL_MAP from "./servicewise_channels_map.json";

function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch (e) {
    return null;
  }
}

async function doRefreshToken(env, providedAccess = null, providedRefresh = null) {
  let access_token = providedAccess || await env.IPTV_SESSIONS.get("nettv_access_token");
  let refresh_token = providedRefresh || await env.IPTV_SESSIONS.get("nettv_refresh_token");

  if (!access_token || !refresh_token) return false;

  const session_data = parseJwt(access_token);
  if (!session_data || !session_data.sid) return false;

  try {
    const response = await fetch('https://auth.geniustv.geniussystems.com.np/v2/subscribers/refresh-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        refresh_token: refresh_token,
        session_id: session_data.sid
      })
    });

    if (!response.ok) throw new Error("Invalid tokens");
    
    const data = await response.json();
    await env.IPTV_SESSIONS.put("nettv_access_token", data.access_token);
    await env.IPTV_SESSIONS.put("nettv_refresh_token", data.refresh_token);
    return true;
  } catch (error) {
    console.error(error);
    return false;
  }
}

async function getAuthSign(env, isRetry = false) {
  const cachedSign = await env.IPTV_SESSIONS.get("nettv_wmsauthsign");
  const lastUpdate = await env.IPTV_SESSIONS.get("nettv_lastupdt");

  if (cachedSign && lastUpdate) {
    const timeDiff = (Date.now() - parseInt(lastUpdate)) / 1000;
    if (timeDiff < 2400) return cachedSign;
  }

  const access_token = await env.IPTV_SESSIONS.get("nettv_access_token");
  
  try {
    const response = await fetch('https://resources.geniustv.geniussystems.com.np/nimble/wmsauthsign/', {
      headers: { "Authorization": `Bearer ${access_token}` }
    });

    if (!response.ok) throw new Error("Failed to fetch sign");

    const data = await response.json();
    await env.IPTV_SESSIONS.put("nettv_wmsauthsign", data.wmsauthsign);
    await env.IPTV_SESSIONS.put("nettv_lastupdt", Date.now().toString());
    
    return data.wmsauthsign;
  } catch (error) {
    if (!isRetry) {
      const refreshed = await doRefreshToken(env);
      if (refreshed) return getAuthSign(env, true);
    }
    return "";
  }
}

const nettvHandlers = {
  async handleGet(request, option, path, env) {
    const wmsauthsign = await getAuthSign(env);
    
    const targetUrl = `https://ott-lb.nettv.com.np/${path}/playlist.m3u8?wmsAuthSign=${wmsauthsign}`;
    return Response.redirect(targetUrl, 302);
  },

  async handlePost(request, option, path, env) {
    try {
      const data = await request.json();
      if (!data.access_token || !data.refresh_token) {
        return new Response("missing parameters", { status: 400 });
      }

      const legit = await doRefreshToken(env, data.access_token, data.refresh_token);
      return new Response(legit ? "SUCCESS" : "INVALID", { status: 200 });
    } catch (e) {
      return new Response("Invalid JSON payload", { status: 400 });
    }
  }
};

const ntvHandlers = {
  async handleGet(request, option, path, env) {
    const response = await fetch(`https://ntv.newitventure.com/api/v1/ntv/home/detail?type=channel&slug=${path}`, {
      headers: { "key": "nitv@123_123" }
    });
    const data = await response.json();
    console.log(path);
    return Response.redirect(data.link, 302);
  }
};

const ufreetvHandlers = {
  async handleGet(request, option, path, env) {
const variants_map = {'2063': '206.212.244.63', '23.9': '23.239.31.26:8989', '41.4': '41.205.93.154', '84.2': '84.17.50.102', '41.2': '41.205.77.102', '23.0': '23.237.104.106:8080', 'rezv': 'rezofoot.tv', 'turm': 'turnerlive.warnermediacdn.com', '41.0': '41.223.30.230', 'cdnv': 'cdn-uw2-prod.tsv2.amagi.tv', 'ipts': 'iptv.domains', '1382': '138.121.15.230:9002', '1900': '190.11.225.124:5000', '41.6': '41.205.70.146', 'trs0': 'trs1.aynaott.com:80', '1989': '198.58.104.90:8989', 'livt': 'liveprodusphoenixeast.global.ssl.fastly.net', 'conm': 'content.uplynk.com', 'tva1': 'tvappapk@ns106911.ip-51-81-106.us:25461', 'strt': 'stream.cammonitorplus.net'};

    const variant = option.includes("-") ? option.split("-")[1] : "23.0";
    const server = variants_map[variant];

    const channelData = CHANNEL_MAP[path];
    if (!channelData || !channelData[option]) {
      return new Response("Channel or variant not found in map", { status: 404 });
    }

    const slug = channelData[option];
    const targetUrl = `http://${server}/${slug}/index.m3u8`;
    
    return Response.redirect(targetUrl, 302);
  }
};

const providers = {
  'nettv': nettvHandlers,
  'ntv': ntvHandlers,
  'ufreetv': ufreetvHandlers
};

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathSegments = url.pathname.split('/').filter(Boolean);

    if (pathSegments.length === 0) {
      return new Response("Nth here.", { status: 200 });
    }

    const option = pathSegments[0];
    const providerKey = option.split('-')[0]; 
    const sourceHandler = providers[providerKey];

    if (!sourceHandler) {
      return new Response("N/A", { status: 404 });
    }

    const path = decodeURIComponent(url.pathname.replace(`/${option}/`, ''));

    if (request.method === 'GET' && sourceHandler.handleGet) {
      return await sourceHandler.handleGet(request, option, path, env);
    }

    if (request.method === 'POST' && sourceHandler.handlePost) {
        return await sourceHandler.handlePost(request, option, path, env);
    }

    return new Response("Not Found", { status: 405 });
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(doRefreshToken(env));
  }
};
