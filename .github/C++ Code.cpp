#include <windows.h>
#include <mmsystem.h>
#pragma comment(lib, "winmm.lib")

INT_PTR CALLBACK AboutDlgProc(HWND hDlg, UINT msg, WPARAM wParam, LPARAM);

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE, LPSTR, int) {
    PlaySound(MAKEINTRESOURCE(ID_SOUND1), hInstance, SND_RESOURCE | SND_SYNC);
    DialogBox(hInstance, MAKEINTRESOURCE(101), NULL, AboutDlgProc);
    return 0;
}

INT_PTR CALLBACK AboutDlgProc(HWND hDlg, UINT msg, WPARAM wParam, LPARAM) {
    if (msg == WM_COMMAND && LOWORD(wParam) == IDOK) {
        EndDialog(hDlg, 0);
        return TRUE;
    }
    return FALSE;
}
