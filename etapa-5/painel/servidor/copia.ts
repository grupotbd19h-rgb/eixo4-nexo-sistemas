// Grava em src/dados.json uma cópia do painel lida no Athena.
//
//    npm run copia
//
// A cópia é o que o painel mostra quando não há servidor por trás (a versão
// publicada como site estático) ou quando a sessão do laboratório expirou. Ela
// sai das mesmas consultas da API, então a cópia e o painel ao vivo não divergem.

import { writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { montarPainel } from './consultas'

const destino = fileURLToPath(new URL('../src/dados.json', import.meta.url))
const { painel, diagnostico } = await montarPainel()
const texto = JSON.stringify(painel, null, 2) + '\n'
try {
  await writeFile(destino, texto, 'utf-8')
} catch (erro) {
  // O "Acesso controlado a pastas" do Windows Defender bloqueia o node.exe de
  // gravar em Documentos (EPERM/EBADF). Nesse caso a cópia vai para a pasta
  // temporária, e o comando para levá-la ao lugar é impresso.
  const codigo = (erro as NodeJS.ErrnoException).code
  if (codigo !== 'EPERM' && codigo !== 'EBADF') throw erro
  const temporario = join(tmpdir(), 'nexo-dados.json')
  await writeFile(temporario, texto, 'utf-8')
  console.warn(
    `Sem permissão para gravar em ${destino} (${codigo}).\n` +
      `Cópia gravada em ${temporario}. Para levá-la ao lugar, no PowerShell:\n` +
      `  Copy-Item "${temporario}" "${destino}"`,
  )
}
console.log(
  `${destino}\n  ${diagnostico.consultas} consultas · ${(diagnostico.bytesLidos / 1024).toFixed(0)} KB lidos · ${(diagnostico.ms / 1000).toFixed(1)} s`,
)
