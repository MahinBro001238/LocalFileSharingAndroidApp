package com.mahin.localfilesharing
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.provider.Settings
import android.os.Bundle
import android.os.Environment
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContentView(R.layout.activity_main)
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this));
        }
        val main = Python.getInstance().getModule("main")
        val message1 = findViewById<TextView>(R.id.Message1)
        val button1 = findViewById<Button>(R.id.Button1)
        val button2 = findViewById<Button>(R.id.Button2)
        val message2 = findViewById<TextView>(R.id.Message2)
        val message3 = findViewById<TextView>(R.id.Message3)
        val password = findViewById<EditText>(R.id.Password)
        val PasswordErrorDialog = AlertDialog.Builder(this)
            .setTitle("Invalid Password")
            .setMessage("Please enter a password")
            .setPositiveButton("Ok", null)
            .create()
        val button3 = findViewById<Button>(R.id.Button3)
        val message4 = findViewById<TextView>(R.id.Message4)
        val button4 = findViewById<Button>(R.id.Button4)
        val message5 = findViewById<TextView>(R.id.Message5)
        val button5 = findViewById<Button>(R.id.Button5)
        val HasStoragePermission = Environment.isExternalStorageManager()
        val HasNotificationPermission = checkSelfPermission(android.Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED
        if (HasStoragePermission && HasNotificationPermission) {
            button3.setOnClickListener() {
                if (password.text.toString().length == 0) {
                    PasswordErrorDialog.show()
                }
                else {
                    message3.visibility = View.GONE
                    password.visibility = View.GONE
                    button3.visibility = View.GONE
                    val intent = Intent(this, LocalFileSharingService::class.java)
                    intent.putExtra("mode", "On")
                    intent.putExtra("password", password.text.toString())
                    ContextCompat.startForegroundService(this, intent)
                    message4.text = "Website Is Running On ${main["get_ip"]?.call()?.toString()}:5002"
                    message4.visibility = View.VISIBLE
                    button4.visibility = View.VISIBLE
                }
            }
            button4.setOnClickListener() {
                message4.visibility = View.GONE
                message4.text = ""
                button4.visibility = View.GONE
                val intent = Intent(this, LocalFileSharingService::class.java)
                intent.putExtra("mode", "Off")
                startService(intent)
                message5.visibility = View.VISIBLE
                button5.visibility = View.VISIBLE
            }
            button5.setOnClickListener() {
                message5.visibility = View.GONE
                button5.visibility = View.GONE
                message3.visibility = View.VISIBLE
                password.text.clear()
                password.visibility = View.VISIBLE
                button3.visibility = View.VISIBLE
            }
            if (main["server_running"]?.call()?.toBoolean() == true) {
                message4.text = "Website Is Running On ${main["get_ip"]?.call()?.toString()}:5002"
                message4.visibility = View.VISIBLE
                button4.visibility = View.VISIBLE
                val intent = Intent(this, LocalFileSharingService::class.java)
                intent.putExtra("mode", "Restore Notification")
                startService(intent)
            }
            else {
                message3.visibility = View.VISIBLE
                password.visibility = View.VISIBLE
                button3.visibility = View.VISIBLE
            }
        }
        else {
            message1.visibility = View.VISIBLE
            button1.visibility = View.VISIBLE
            button2.visibility = View.VISIBLE
            message2.visibility = View.VISIBLE
            button1.setOnClickListener() {
                val intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                intent.data = Uri.parse("package:$packageName")
                startActivity(intent)
            }
            button2.setOnClickListener() {
                requestPermissions(
                    arrayOf(android.Manifest.permission.POST_NOTIFICATIONS),
                    1
                )
            }
        }
    }
}