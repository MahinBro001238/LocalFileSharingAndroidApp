package com.mahin.localfilesharing
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.chaquo.python.Python
class LocalFileSharingService : Service() {
    override fun onBind(intent: Intent?): IBinder? {
        return null
    }
    private fun ShowNotification() {
        val ChannelID = "LocalFileSharingChannel"
        val channel = NotificationChannel(
            ChannelID,
            "Local File Sharing",
            NotificationManager.IMPORTANCE_LOW
        )
        getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        val notification = NotificationCompat.Builder(this, ChannelID)
            .setContentTitle("Local File Sharing")
            .setContentText("Local File Sharing is running")
            .setSmallIcon(R.drawable.ic_notification)
            .setOngoing(true)
            .build()
        startForeground(1, notification)
    }
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val main = Python.getInstance().getModule("main")
        val mode = intent?.getStringExtra("mode")
        if (mode == "On") {
            ShowNotification()
            val password = intent.getStringExtra("password")
            main["start_local_file_sharing"]?.call(password)
        }
        else if (mode == "Restore Notification") {
            ShowNotification()
        }
        else {
            main["stop_local_file_sharing"]?.call()
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
        }
        return START_STICKY
    }
}