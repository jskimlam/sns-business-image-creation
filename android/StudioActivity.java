package io.github.jskimlam.panhyeong;

import android.app.Activity;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.*;
import android.widget.Toast;
import java.io.*;

public final class StudioActivity extends Activity {
    private WebView web;
    private static final String CHAT = "com.openai.chatgpt";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        web = new WebView(this);
        web.setBackgroundColor(Color.rgb(244,243,236));
        web.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                         insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        setContentView(web);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.getSettings().setBlockNetworkLoads(true);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) { return true; }
        });
        web.setWebChromeClient(new WebChromeClient());
        web.addJavascriptInterface(new Bridge(), "MobileStudio");
        try (InputStream input = getAssets().open("studio-mobile.html")) {
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int n;
            while ((n=input.read(buffer))!=-1) bytes.write(buffer,0,n);
            web.loadDataWithBaseURL("https://studio.invalid/",bytes.toString("UTF-8"),"text/html","UTF-8",null);
        } catch(IOException ex) {
            toast("제작 화면을 열 수 없습니다.");
        }
    }

    private void toast(String text) { Toast.makeText(this,text,Toast.LENGTH_LONG).show(); }
    public final class Bridge {
        @JavascriptInterface public void handoff(String brief, boolean open) {
            if (brief == null || brief.trim().isEmpty()) return;
            runOnUiThread(() -> {
                try {
                    ((ClipboardManager)getSystemService(CLIPBOARD_SERVICE)).setPrimaryClip(ClipData.newPlainText("이미지 제작 지시문",brief));
                } catch(RuntimeException e) { toast("복사에 실패했습니다. 지시문을 길게 눌러 복사하세요."); return; }
                if (!open) { toast("제작 지시문을 복사했습니다."); return; }
                Intent launch=getPackageManager().getLaunchIntentForPackage(CHAT);
                try {
                    if(launch!=null) startActivity(launch);
                    else startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://chatgpt.com/")));
                } catch(ActivityNotFoundException e) { toast("지시문을 복사했습니다. ChatGPT를 직접 열어 주세요."); }
            });
        }
    }
}
