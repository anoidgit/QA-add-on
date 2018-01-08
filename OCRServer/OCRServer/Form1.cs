using OneNoteOCRDll;
using System;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using ZeroMQ;

namespace OCRServer
{
    public partial class Form1 : Form
    {
        private bool running = false;
        private OneNoteOCR ocr = new OneNoteOCR();

        private string ocrIMG(string imgf, OneNoteOCR eng)
        {
            string rs = "";
            var text = eng.RecognizeImage(imgf);
            if (text != null)
            {
                rs = text;
            }
            return rs;
        }
        private void server()
        {
            if (running)
            {
                using (var context = new ZContext())
                using (var responder = new ZSocket(context, ZSocketType.REP))
                {
                    responder.Bind("tcp://" + textBox1.Text);
                    while (running)
                    {
                        using (ZFrame request = responder.ReceiveFrame())
                        {
                            responder.Send(new ZFrame(Encoding.UTF8.GetBytes(ocrIMG(request.ReadString(), ocr))));
                        }
                    }
                }
            }
        }
        private void stopServer()
        {
            running = false;
        }
        private void startServer()
        {
            running = true;
            Thread th = new Thread(server);
            th.Start();
        }
        public Form1()
        {
            InitializeComponent();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            if (running)
            {
                stopServer();
                button1.Text = "启动";
            }
            else
            {
                startServer();
                button1.Text = "停止";
            }
        }
    }
}
